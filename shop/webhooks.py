import stripe
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Order
from .emails import send_download_link_email

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        return HttpResponse(status=400)

    event_type = event["type"]
    payment_intent = event["data"]["object"]

    if event_type == "payment_intent.succeeded":
        handle_payment_intent_succeeded(payment_intent)
    elif event_type == "payment_intent.payment_failed":
        handle_payment_intent_failed(payment_intent)

    return HttpResponse(status=200)


def handle_payment_intent_succeeded(payment_intent):
    order = Order.objects.filter(
        payment_intent_id=payment_intent.id, status="pending"
    ).first()

    if order:
        order.status = "completed"
        order.paid = True
        order.save()

        for order_item in order.items.all():
            product = order_item.product
            product.purchase_count += order_item.quantity
            product.save()

        try:
            for order_item in order.items.all():
                send_download_link_email(order_item)
                from .emails import send_admin_new_order_email

                send_admin_new_order_email(order)

        except Exception as e:
            logger.error(f"Error sending download emails in webhook: {str(e)}")


def handle_payment_intent_failed(payment_intent):
    order = Order.objects.filter(
        payment_intent_id=payment_intent.id, status="pending"
    ).first()

    if order:
        order.status = "failed"
        order.save()
