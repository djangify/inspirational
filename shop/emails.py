from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger("shop.emails")


def send_order_confirmation_email(order):
    try:
        items_data = [
            {
                "name": item.product.title,
                "price": (item.price_paid_pence * item.quantity) / 100,
                "quantity": item.quantity,
                "downloads_remaining": item.downloads_remaining,
            }
            for item in order.items.all()
        ]

        context = {
            "order_id": order.order_id,
            "first_name": order.user.first_name if order.user else "",
            "email": order.email,
            "items": items_data,
            "total": order.total_price,
            "site_url": settings.SITE_URL,
            "user_name": order.user.get_full_name() if order.user else None,
            "date_created": order.created.strftime("%Y-%m-%d %H:%M:%S"),
        }

        html_content = render_to_string(
            "accounts/email/order_confirmation.html", context
        )
        text_content = strip_tags(html_content)

        subject = f"Order Confirmation #{order.order_id}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [order.email]

        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        logger.info(
            f"Order confirmation email sent for order {order.order_id} to {order.email}"
        )
    except Exception as e:
        logger.error(
            f"Failed to send order confirmation email for order {order.order_id}: {str(e)}"
        )
        raise


def send_admin_new_order_email(order):
    """Notify admin when a new order has been completed."""
    try:
        items_data = [
            f"- {item.product.title} (x{item.quantity}) — ${item.get_cost():.2f}"
            for item in order.items.all()
        ]
        items_list = "\n".join(items_data)

        subject = f"New Order Received — #{order.order_id}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [settings.DEFAULT_FROM_EMAIL]

        message = (
            f"A new order has been completed on Inspirational Guidance.\n\n"
            f"Order ID: {order.order_id}\n"
            f"Customer: {order.email}\n"
            f"Status: {order.status}\n"
            f"Total: ${order.get_total_cost():.2f}\n\n"
            f"Items:\n{items_list}\n\n"
            f"View order in admin:\n"
            f"{settings.SITE_URL}/admin/shop/order/{order.id}/change/"
        )

        msg = EmailMultiAlternatives(subject, message, from_email, to_email)
        msg.send()

        logger.info(f"Admin notified of new order {order.order_id}")
    except Exception as e:
        logger.error(
            f"Failed to send admin new order email for {order.order_id}: {str(e)}"
        )
        raise
