# shop/views.py
from .models import Category, Product, Order, OrderItem, ShopSettings, OrderBump, Coupon, OneTimeOffer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import mail_admins
from django.http import HttpResponse, HttpResponseBadRequest, FileResponse, Http404
from django.views.decorators.http import require_POST, require_http_methods
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import stripe
import os
import logging
from decimal import Decimal
from django.db.models import Q
from django.urls import reverse
import mimetypes
from django.utils import timezone
from datetime import timedelta
from .models import DownloadLog
from shop.forms import GuestDetailsForm, ProductReviewForm
from .emails import send_order_confirmation_email, send_admin_new_order_email
from .cart import Cart


stripe.api_key = settings.STRIPE_SECRET_KEY

# Set up logger
logger = logging.getLogger("shop")


def product_list(request):
    categories = Category.objects.all()
    query = request.GET.get("q", "").strip()

    products = Product.objects.filter(
        is_active=True, status__in=["publish", "soon", "full"]
    ).exclude(id__in=OneTimeOffer.hidden_product_ids()).order_by("order", "-created")

    if query:
        products = products.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    paginator = Paginator(products, 20)
    page = request.GET.get("page")
    products = paginator.get_page(page)

    return render(
        request,
        "shop/list.html",
        {
            "products": products,
            "categories": categories,
            "current_category": None,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
            "query": query,
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product, slug=slug, is_active=True, status__in=["publish", "soon", "full"]
    )

    # The one-time offer product is reserved for the offer page only.
    hidden_ids = OneTimeOffer.hidden_product_ids()
    if product.id in hidden_ids:
        raise Http404("Product not available.")

    related_products = Product.objects.filter(
        category=product.category,
        status__in=["publish", "full"],
        is_active=True,
    ).exclude(id=product.id).exclude(id__in=hidden_ids)[:3]

    has_purchased = False
    order_item = None
    review_form = None

    if request.user.is_authenticated:
        order_item = OrderItem.objects.filter(
            order__user=request.user, order__paid=True, product=product
        ).first()

        has_purchased = bool(order_item)
        review_form = ProductReviewForm() if product.can_review(request.user) else None

    # fetch additional images
    images = product.images.all()

    return render(
        request,
        "shop/detail.html",
        {
            "product": product,
            "related_products": related_products,
            "has_purchased": has_purchased,
            "order_item": order_item,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
            "form": review_form,
            "images": images,
            "request": request,
        },
    )


@require_POST
def cart_add(request, product_id):
    try:
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get("quantity", 1))
        cart.add(product=product, quantity=quantity)
        messages.success(request, f"{product.title} has been added to your cart.")
        return redirect("shop:cart_detail")
    except Exception as e:
        messages.error(request, "There was an error adding the item to your cart.")
        return redirect("shop:product_list")


def category_hub(request):
    categories = Category.objects.all()
    return render(request, "shop/category_hub.html", {"categories": categories})


def cart_detail(request):
    try:
        cart = Cart(request)
        return render(request, "shop/cart.html", {"cart": cart})
    except Exception as e:
        print(f"Error in cart detail: {str(e)}")
        messages.error(request, "There was an error displaying your cart.")
        return redirect("shop:product_list")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect("shop:cart_detail")


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get("quantity", 1))
    cart.add(product=product, quantity=quantity, override_quantity=True)
    return redirect("shop:cart_detail")


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, "Your cart is empty.")
        return redirect("shop:cart_detail")

    guest_form = None
    if not request.user.is_authenticated:
        if request.method == "POST":
            guest_form = GuestDetailsForm(request.POST)
            if guest_form.is_valid():
                request.session["guest_details"] = {
                    "first_name": guest_form.cleaned_data["first_name"],
                    "last_name": guest_form.cleaned_data["last_name"],
                    "email": guest_form.cleaned_data["email"],
                    "phone": guest_form.cleaned_data["phone"],
                }
            else:
                return HttpResponseBadRequest("Invalid form data")
        else:
            guest_form = GuestDetailsForm()

    try:
        total_price = cart.get_total_price()

        if total_price <= 0:
            messages.error(request, "Invalid cart total")
            return redirect("shop:cart_detail")

        # --- Order Bump logic ---
        cart_product_ids = [int(k) for k in cart.cart.keys()]

        accepted_bump_product_id = request.session.get("order_bump_product_id")
        bump_accepted = False
        active_bump = None
        accepted_bump = None

        eligible_bumps = (
            OrderBump.objects.filter(is_active=True)
            .filter(
                Q(trigger_product__isnull=True)
                | Q(trigger_product_id__in=cart_product_ids)
            )
            .exclude(bump_product_id__in=cart_product_ids)
            .filter(bump_product__is_active=True)
            .select_related("bump_product", "trigger_product")
            .order_by("order")
        )

        if accepted_bump_product_id:
            accepted_bump = (
                OrderBump.objects.filter(
                    is_active=True,
                    bump_product_id=accepted_bump_product_id,
                )
                .select_related("bump_product")
                .first()
            )
            if accepted_bump:
                bump_accepted = True
                total_price += accepted_bump.bump_price
                active_bump = eligible_bumps.exclude(
                    bump_product_id=accepted_bump_product_id
                ).first()
            else:
                request.session.pop("order_bump_product_id", None)
                active_bump = eligible_bumps.first()
        else:
            active_bump = eligible_bumps.first()
        # --- End Order Bump logic ---

        # --- Coupon logic ---
        coupon_code = request.session.get("coupon_code", "")
        coupon_discount_pence = request.session.get("coupon_discount_pence", 0)
        coupon_discount = Decimal(coupon_discount_pence) / 100

        if coupon_discount > 0:
            # Stripe minimum charge is $0.50 — never go below that
            total_price = max(total_price - coupon_discount, Decimal("0.50"))
        # --- End Coupon logic ---

        payment_intent_data = {
            "amount": int(round(total_price * 100)),
            "currency": "usd",
            "payment_method_types": ["card"],
            "metadata": {
                "user_id": (
                    str(request.user.id) if request.user.is_authenticated else "guest"
                ),
                "is_guest": str(not request.user.is_authenticated),
                "order_bump_product_id": str(accepted_bump_product_id) if bump_accepted else "",
                "coupon_code": coupon_code,
            },
        }

        if request.user.is_authenticated:
            payment_intent_data["receipt_email"] = request.user.email
        elif "guest_details" in request.session:
            payment_intent_data["receipt_email"] = request.session["guest_details"][
                "email"
            ]

        intent = stripe.PaymentIntent.create(**payment_intent_data)

        # Save cart snapshot keyed to this PaymentIntent
        # so payment_success can recover it even if session cart is lost
        request.session[f"cart_snapshot_{intent.id}"] = [
            {
                "product_id": item["product"].id,
                "quantity": item["quantity"],
                "price": float(item["price"]),
            }
            for item in cart
        ]
        request.session.modified = True

        shop_settings = ShopSettings.get_settings()

        context = {
            "client_secret": intent.client_secret,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
            "cart": cart,
            "guest_form": guest_form,
            "is_guest": not request.user.is_authenticated,
            "payment_intent_id": intent.id,
            "show_withdrawal_consent": shop_settings.show_digital_withdrawal_consent,
            "withdrawal_consent_text": shop_settings.digital_withdrawal_consent_text,
            # Order bump
            "active_bump": active_bump,
            "accepted_bump": accepted_bump,
            "bump_accepted": bump_accepted,
            # Coupon
            "checkout_total": total_price,
            "applied_coupon_code": coupon_code,
            "coupon_discount": coupon_discount,
        }

        return render(request, "shop/checkout.html", context)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        messages.error(request, f"Payment processing error: {str(e)}")
        return redirect("shop:cart_detail")
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        messages.error(request, "An error occurred during checkout. Please try again.")
        return redirect("shop:cart_detail")


def payment_success(request):
    payment_intent_id = request.GET.get("payment_intent")
    if not payment_intent_id:
        messages.error(request, "No payment information found.")
        return redirect("shop:cart_detail")

    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if payment_intent.status != "succeeded":
            logger.warning(f"Payment intent {payment_intent_id} not succeeded")
            messages.error(request, "Payment was not successful.")
            return redirect("shop:cart_detail")

        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to complete checkout.")
            return redirect("accounts:login")

        # Prevent duplicate order creation on refresh
        existing_order = Order.objects.filter(
            payment_intent_id=payment_intent_id
        ).first()
        if existing_order:
            return redirect("shop:purchases")

        # Try snapshot first, fall back to live cart
        snapshot_key = f"cart_snapshot_{payment_intent_id}"
        cart_snapshot = request.session.get(snapshot_key)
        live_cart = Cart(request)

        coupon_code_session = request.session.get("coupon_code", "")
        coupon_discount_pence_session = request.session.get("coupon_discount_pence", 0)

        order = Order.objects.create(
            user=request.user,
            email=request.user.email,
            payment_intent_id=payment_intent_id,
            paid=True,
            status="completed",
            coupon_code=coupon_code_session,
            coupon_discount_pence=coupon_discount_pence_session,
        )

        items_created = 0

        if cart_snapshot:
            # Use the snapshot saved at checkout time
            for item_data in cart_snapshot:
                try:
                    product = Product.objects.get(id=item_data["product_id"])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price_paid_pence=int(item_data["price"] * 100),
                        quantity=item_data["quantity"],
                    )
                    product.purchase_count += item_data["quantity"]
                    product.save()
                    items_created += 1
                except Product.DoesNotExist:
                    logger.error(
                        f"Product {item_data['product_id']} not found in snapshot"
                    )
        else:
            # Fallback to live cart
            logger.warning(
                f"No cart snapshot found for {payment_intent_id}, using live cart"
            )
            for item in live_cart:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    price_paid_pence=int(item["price"] * 100),
                    quantity=item["quantity"],
                )
                product = item["product"]
                product.purchase_count += item["quantity"]
                product.save()
                items_created += 1

        # --- Order Bump: create OrderItem if accepted ---
        bump_product_id = request.session.get("order_bump_product_id")
        if bump_product_id:
            try:
                bump_product = Product.objects.get(id=bump_product_id)
                OrderItem.objects.create(
                    order=order,
                    product=bump_product,
                    price_paid_pence=bump_product.sale_price_pence or bump_product.price_pence,
                    quantity=1,
                )
                bump_product.purchase_count += 1
                bump_product.save()
                items_created += 1
            except Exception as e:
                logger.error(f"Error adding bump product to order {order.order_id}: {str(e)}")
            finally:
                request.session.pop("order_bump_product_id", None)
        # --- End Order Bump ---

        # --- Coupon: increment times_used and clear session ---
        if coupon_code_session:
            try:
                coupon = Coupon.objects.get(code=coupon_code_session)
                coupon.times_used += 1
                coupon.save(update_fields=["times_used"])
            except Exception as e:
                logger.error(f"Error updating coupon usage for order {order.order_id}: {str(e)}")
            finally:
                request.session.pop("coupon_code", None)
                request.session.pop("coupon_discount_pence", None)
        # --- End Coupon ---

        if items_created == 0:
            logger.error(
                f"Order {order.order_id} created with 0 items - payment_intent: {payment_intent_id}"
            )
            mail_admins(
                subject=f"URGENT: Order {order.order_id} created with 0 items",
                message=f"Payment succeeded but no items were created.\nPayment Intent: {payment_intent_id}\nCustomer: {request.user.email}",
                fail_silently=True,
            )

        try:
            send_order_confirmation_email(order)
            from .emails import send_admin_new_order_email

            send_admin_new_order_email(order)
        except Exception as e:
            logger.error(f"Failed to send order emails for {order.order_id}: {str(e)}")

        # Clean up snapshot and cart
        if snapshot_key in request.session:
            del request.session[snapshot_key]
        live_cart.clear()
        request.session.modified = True

        return render(request, "shop/success.html", {"order": order})

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        messages.error(request, f"Payment processing error: {str(e)}")
        return redirect("shop:cart_detail")

    except Exception as e:
        logger.error(f"Unexpected error in payment_success: {str(e)}")
        messages.error(request, "There was an error processing your order.")
        return redirect("shop:cart_detail")


def payment_cancel(request):
    messages.error(request, "Payment was cancelled.")
    return redirect("shop:cart_detail")


@login_required
def purchases(request):
    orders = Order.objects.filter(user=request.user).order_by("-created")
    return render(request, "shop/purchases.html", {"orders": orders})


def category_list(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(
        category=category, status__in=["publish", "soon", "full"], is_active=True
    ).exclude(id__in=OneTimeOffer.hidden_product_ids()).order_by("order", "-created")
    categories = Category.objects.all()

    paginator = Paginator(products, 20)
    page = request.GET.get("page")
    products = paginator.get_page(page)

    return render(
        request,
        "shop/list.html",
        {
            "products": products,
            "categories": categories,
            "current_category": category,
            "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        },
    )


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-created")
    return render(request, "shop/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, "shop/purchases.html", {"order": order})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Something failed: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Something failed: {str(e)}")
        return HttpResponse(status=400)

    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object
        handle_successful_payment(payment_intent)
    elif event.type == "payment_intent.payment_failed":
        payment_intent = event.data.object
        handle_failed_payment(payment_intent)

    return HttpResponse(status=200)


def handle_successful_payment(payment_intent):
    order = Order.objects.filter(payment_intent_id=payment_intent.id).first()
    if order and not order.paid:
        order.paid = True
        order.status = "completed"
        order.save()
        try:
            send_order_confirmation_email(order)
            send_admin_new_order_email(order)
        except Exception as e:
            logger.error(f"Error sending emails for order {order.order_id}: {str(e)}")


def handle_failed_payment(payment_intent):
    order = Order.objects.filter(payment_intent_id=payment_intent.id).first()
    if order:
        order.status = "failed"
        order.save()


@login_required
@require_http_methods(["GET"])
def secure_download(request, order_item_id):
    order_item = get_object_or_404(OrderItem, id=order_item_id)

    if order_item.order.user != request.user:
        messages.error(request, "You do not have permission to access this file.")
        return redirect("shop:order_history")

    if not order_item.product.files:
        messages.error(request, "File not available for this product.")
        return redirect("shop:order_history")

    if order_item.download_count >= order_item.product.download_limit:
        logger.warning(f"Download limit reached for OrderItem {order_item.id}")
        messages.error(request, "You have reached your download limit.")
        return redirect("shop:order_history")

    recent_download = DownloadLog.objects.filter(
        order_item=order_item,
        user=request.user,
        downloaded_at__gte=timezone.now() - timedelta(seconds=2),
    ).exists()

    if not recent_download:
        order_item.download_count += 1
        order_item.save()
        DownloadLog.objects.create(order_item=order_item, user=request.user)

    file_path = order_item.product.files.path

    if not os.path.exists(file_path):
        error_msg = f"File missing for OrderItem {order_item.id} | Path: {file_path}"
        logger.error(error_msg)
        mail_admins(subject="Download Failure: File Missing", message=error_msg, fail_silently=True)
        messages.error(request, "File could not be found.")
        return redirect("shop:order_history")

    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or "application/octet-stream"
    response = FileResponse(open(file_path, "rb"), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not request.user.is_superuser:
        if not product.can_review(request.user):
            messages.error(request, "You can only review products you have purchased.")
            return redirect("shop:product_detail", slug=product.slug)

    if request.method == "POST":
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.verified_purchase = True
            review.save()
            messages.success(request, "Your review has been added.")
            return redirect("shop:product_detail", slug=product.slug)
    else:
        form = ProductReviewForm()

    return render(request, "shop/add_review.html", {"form": form, "product": product})


# ============================================================
# ONE-TIME OFFER VIEWS  (post-registration tripwire)
# ============================================================

def _mark_oto_seen(user):
    """Stamp the user's profile so the offer can never show again."""
    profile = getattr(user, "profile", None)
    if profile is not None and profile.oto_seen_at is None:
        profile.oto_seen_at = timezone.now()
        profile.save(update_fields=["oto_seen_at"])


@login_required
def one_time_offer(request):
    """
    Display the one-time offer with an embedded Stripe payment form. Marks the
    offer as 'seen' on render so it is strictly one-time. Staff can add
    ?preview=1 to view the page without becoming ineligible or being stamped.
    """
    offer = OneTimeOffer.objects.select_related("product").first()

    preview = request.GET.get("preview") == "1" and request.user.is_staff

    # Not configured / not eligible -> straight to the dashboard.
    if not offer or (not preview and not offer.is_eligible_for(request.user)):
        return redirect("accounts:dashboard")

    product = offer.product

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=offer.price_pence,
            currency="usd",
            payment_method_types=["card"],
            metadata={
                "user_id": str(request.user.id),
                "oto": "1",
                "product_id": str(product.id),
            },
            receipt_email=request.user.email,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error building one-time offer: {str(e)}")
        if not preview:
            _mark_oto_seen(request.user)
        return redirect("accounts:dashboard")

    # Digital withdrawal consent (EU/UK) — reuse the shop-wide setting.
    shop_settings = ShopSettings.objects.first()
    show_withdrawal_consent = (
        shop_settings.show_digital_withdrawal_consent if shop_settings else False
    )
    withdrawal_consent_text = (
        shop_settings.digital_withdrawal_consent_text if shop_settings else ""
    )

    # One-time guarantee: stamp now that we have a valid intent + page to show.
    if not preview:
        _mark_oto_seen(request.user)

    context = {
        "offer": offer,
        "product": product,
        "offer_price": offer.price,
        "normal_price": offer.normal_price,
        "has_special_price": offer.has_special_price,
        "client_secret": intent.client_secret,
        "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "payment_intent_id": intent.id,
        "show_withdrawal_consent": show_withdrawal_consent,
        "withdrawal_consent_text": withdrawal_consent_text,
        "preview": preview,
    }
    return render(request, "shop/one_time_offer.html", context)


@login_required
def one_time_offer_success(request):
    """
    Stripe return target. Creates a single-item completed order for the offer
    product, mirroring checkout.payment_success. Downloads are accessed via the
    account — no cart involved.
    """
    payment_intent_id = request.GET.get("payment_intent")
    if not payment_intent_id:
        messages.error(request, "No payment information found.")
        return redirect("accounts:dashboard")

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if payment_intent.status != "succeeded":
            messages.error(request, "Payment was not successful.")
            return redirect("accounts:dashboard")

        # Prevent duplicate orders (also guards against the webhook racing us).
        existing_order = Order.objects.filter(
            payment_intent_id=payment_intent_id
        ).first()
        if existing_order:
            return redirect("shop:purchases")

        offer = OneTimeOffer.objects.select_related("product").first()
        if not offer:
            messages.error(request, "This offer is no longer available.")
            return redirect("accounts:dashboard")

        product = offer.product

        order = Order.objects.create(
            user=request.user,
            email=request.user.email,
            payment_intent_id=payment_intent_id,
            paid=True,
            status="completed",
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price_paid_pence=offer.price_pence,
            quantity=1,
        )

        product.purchase_count += 1
        product.save()

        # Bundle: unlock every included product (download + existing AI coach)
        # by creating a completed £0 line item for each.
        for bundled in offer.included_products.all():
            OrderItem.objects.create(
                order=order,
                product=bundled,
                price_paid_pence=0,
                quantity=1,
            )
            bundled.purchase_count += 1
            bundled.save(update_fields=["purchase_count"])

        # Confirmation emails (order + admin) — best effort.
        try:
            send_order_confirmation_email(order)
            send_admin_new_order_email(order)
        except Exception as e:
            logger.error(f"Error sending OTO emails for order {order.order_id}: {str(e)}")

        messages.success(request, "Thank you! Your purchase is in your account.")
        return redirect("shop:purchases")

    except Exception as e:
        logger.error(f"Error in one_time_offer_success: {str(e)}")
        messages.error(request, "There was an error processing your order.")
        return redirect("accounts:dashboard")


@login_required
def one_time_offer_decline(request):
    """Customer declined the offer. Ensure it's marked seen, go to dashboard."""
    _mark_oto_seen(request.user)
    return redirect("accounts:dashboard")


# ============================================================
# ORDER BUMP & COUPON VIEWS
# ============================================================

@require_POST
def toggle_order_bump(request):
    product_id = request.POST.get("product_id") or request.POST.get("bump_product_id")
    if not product_id:
        return HttpResponse(status=400)

    current = request.session.get("order_bump_product_id")
    if str(current) == str(product_id):
        request.session.pop("order_bump_product_id", None)
    else:
        request.session["order_bump_product_id"] = int(product_id)

    checkout_url = reverse("shop:checkout")
    if request.headers.get("HX-Request"):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = checkout_url
        return response
    return redirect(checkout_url)


@require_POST
def apply_coupon(request):
    from .models import Coupon
    code = request.POST.get("coupon_code", "").strip().upper()
    checkout_url = reverse("shop:checkout")

    if not code:
        error_html = '<p class="text-red-600 text-sm mt-1">Please enter a coupon code.</p>'
        if request.headers.get("HX-Request"):
            return HttpResponse(error_html, status=200)
        return redirect(checkout_url)

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        error_html = f'<p class="text-red-600 text-sm mt-1">"{code}" is not a valid coupon code.</p>'
        if request.headers.get("HX-Request"):
            return HttpResponse(error_html, status=200)
        return redirect(checkout_url)

    from .cart import Cart
    cart = Cart(request)
    cart_total_pence = int(round(sum(
        (item["product"].sale_price_pence or item["product"].price_pence) * item["quantity"]
        for item in cart
    )))

    valid, message = coupon.is_valid(cart_total_pence)
    if not valid:
        error_html = f'<p class="text-red-600 text-sm mt-1">{message}</p>'
        if request.headers.get("HX-Request"):
            return HttpResponse(error_html, status=200)
        return redirect(checkout_url)

    discount_pence = coupon.calculate_discount_pence(cart_total_pence)
    request.session["coupon_code"] = coupon.code
    request.session["coupon_discount_pence"] = discount_pence

    if request.headers.get("HX-Request"):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = checkout_url
        return response
    return redirect(checkout_url)


@require_POST
def remove_coupon(request):
    request.session.pop("coupon_code", None)
    request.session.pop("coupon_discount_pence", None)
    return redirect(reverse("shop:checkout"))
