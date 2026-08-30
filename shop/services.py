# shop/services.py
"""
Order finalisation shared by the browser-redirect handler (views.payment_success)
and the Stripe webhook (webhooks.handle_payment_intent_succeeded).

Both entry points call finalize_order_from_payment_intent(), which builds the
completed Order from the server-side PendingCheckout snapshot. It is idempotent:
whichever path arrives first creates the Order; the other becomes a no-op. This
guarantees a paid customer always gets an Order even if their browser never
returns to the success page.
"""
import logging

from django.core.mail import mail_admins
from django.db import transaction

from .models import Order, OrderItem, Product, PendingCheckout, Coupon
from .emails import send_order_confirmation_email, send_admin_new_order_email

logger = logging.getLogger("shop")


def finalize_order_from_payment_intent(payment_intent_id):
    """
    Idempotently create the completed Order for a succeeded PaymentIntent from
    its PendingCheckout snapshot.

    Returns the Order, or None if there is no snapshot to build from (in which
    case the caller/admin is alerted). Safe to call multiple times and from
    multiple processes concurrently.
    """
    # Fast path: order already exists (created by the other entry point, or by a
    # page refresh) — nothing to do.
    existing = Order.objects.filter(payment_intent_id=payment_intent_id).first()
    if existing:
        return existing

    try:
        with transaction.atomic():
            # Lock the snapshot row so a simultaneous redirect + webhook serialise
            # here and only one of them creates the Order.
            pending = (
                PendingCheckout.objects.select_for_update()
                .filter(payment_intent_id=payment_intent_id)
                .first()
            )

            # Re-check inside the lock in case the other path just created it.
            existing = Order.objects.filter(
                payment_intent_id=payment_intent_id
            ).first()
            if existing:
                return existing

            if pending is None:
                logger.error(
                    "No PendingCheckout snapshot for %s — cannot build order. "
                    "Payment succeeded but order NOT created.",
                    payment_intent_id,
                )
                mail_admins(
                    subject="URGENT: paid PaymentIntent with no checkout snapshot",
                    message=(
                        f"PaymentIntent {payment_intent_id} succeeded but there is "
                        f"no PendingCheckout to build an order from. Investigate and "
                        f"create the order manually."
                    ),
                    fail_silently=True,
                )
                return None

            order = Order.objects.create(
                user=pending.user,
                email=pending.email,
                payment_intent_id=payment_intent_id,
                paid=True,
                status="completed",
                coupon_code=pending.coupon_code,
                coupon_discount_pence=pending.coupon_discount_pence,
            )

            items_created = 0
            for item in pending.items or []:
                try:
                    product = Product.objects.get(id=item["product_id"])
                except Product.DoesNotExist:
                    logger.error(
                        "Product %s missing while finalizing %s",
                        item.get("product_id"),
                        payment_intent_id,
                    )
                    continue
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price_paid_pence=int(round(float(item["price"]) * 100)),
                    quantity=item["quantity"],
                )
                product.purchase_count += item["quantity"]
                product.save(update_fields=["purchase_count"])
                items_created += 1

            # Order bump
            if pending.bump_product_id:
                try:
                    bump = Product.objects.get(id=pending.bump_product_id)
                    OrderItem.objects.create(
                        order=order,
                        product=bump,
                        price_paid_pence=bump.sale_price_pence or bump.price_pence,
                        quantity=1,
                    )
                    bump.purchase_count += 1
                    bump.save(update_fields=["purchase_count"])
                    items_created += 1
                except Product.DoesNotExist:
                    logger.error(
                        "Bump product %s missing for %s",
                        pending.bump_product_id,
                        payment_intent_id,
                    )

            # Coupon usage
            if pending.coupon_code:
                try:
                    coupon = Coupon.objects.get(code=pending.coupon_code)
                    coupon.times_used += 1
                    coupon.save(update_fields=["times_used"])
                except Coupon.DoesNotExist:
                    pass

            pending.fulfilled = True
            pending.save(update_fields=["fulfilled"])

        # --- side effects after the transaction commits ---
        if items_created == 0:
            logger.error(
                "Order %s finalized with 0 items (%s)",
                order.order_id,
                payment_intent_id,
            )
            mail_admins(
                subject=f"URGENT: Order {order.order_id} created with 0 items",
                message=(
                    f"PaymentIntent {payment_intent_id} succeeded but no items were "
                    f"created for order {order.order_id}."
                ),
                fail_silently=True,
            )

        try:
            send_order_confirmation_email(order)
            send_admin_new_order_email(order)
        except Exception as e:
            logger.error(
                "Failed to send order emails for %s: %s", order.order_id, str(e)
            )

        return order

    except Exception as e:
        logger.error(
            "Error finalizing order for %s: %s", payment_intent_id, str(e)
        )
        return None
