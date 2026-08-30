import stripe
import logging
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Order
from .services import finalize_order_from_payment_intent

logger = logging.getLogger("shop")


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
    """
    Safety net for the browser-redirect flow: build (or confirm) the Order from
    the server-side PendingCheckout snapshot. Idempotent — if payment_success
    already created the Order, this is a no-op. If the browser never returned,
    this is what actually creates the customer's Order.
    """
    order = finalize_order_from_payment_intent(payment_intent.id)
    if order:
        logger.info(
            "Webhook finalized order %s for payment_intent %s",
            order.order_id,
            payment_intent.id,
        )


def handle_payment_intent_failed(payment_intent):
    order = Order.objects.filter(
        payment_intent_id=payment_intent.id, status="pending"
    ).first()

    if order:
        order.status = "failed"
        order.save()
