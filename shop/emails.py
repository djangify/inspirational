from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.conf import settings
import logging

# Set up logger
logger = logging.getLogger("shop.emails")


def send_order_confirmation_email(order):
    try:
        # Prepare serializable order items data
        items_data = [
            {
                "name": item.product.title,
                "price": (item.price_paid_pence * item.quantity)
                / 100,  # Calculate total price for quantity
                "quantity": item.quantity,
                "downloads_remaining": item.downloads_remaining,
            }
            for item in order.items.all()
        ]

        context = {
            "order_id": order.order_id,
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
            f"Order confirmation email sent successfully for order {order.order_id} to {order.email}"
        )
    except Exception as e:
        logger.error(
            f"Failed to send order confirmation email for order {order.order_id}: {str(e)}"
        )
        raise


def send_download_link_email(order_item):
    """Send download link email for any product type"""
    try:
        # Get the appropriate download URL
        download_url = None
        if order_item.product.files:
            download_url = f"{settings.SITE_URL}{reverse('shop:secure_download', args=[order_item.id])}"
        elif order_item.product.get_download_url():
            download_url = f"{settings.SITE_URL}{reverse('shop:secure_download', args=[order_item.id])}"

        if not download_url:
            logger.warning(f"No download URL available for order item {order_item.id}")
            return

        # Get number of downloads remaining
        if order_item.product.product_type == "download":
            downloads_remaining = (
                order_item.downloads_remaining - order_item.download_count
            )
        else:
            downloads_remaining = "Unlimited"  # For tuition PDFs

        context = {
            "order_item": order_item,
            "product": order_item.product,
            "download_url": download_url,
            "site_url": settings.SITE_URL,
            "downloads_remaining": downloads_remaining,
        }

        if order_item.order.user:
            context["user"] = order_item.order.user
            to_email = order_item.order.user.email
        else:
            to_email = order_item.order.email

        html_content = render_to_string("accounts/email/download_link.html", context)
        text_content = strip_tags(html_content)

        subject = f"Your Download Link - {order_item.product.title}"
        from_email = settings.DEFAULT_FROM_EMAIL

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        logger.info(
            f"Download link email sent successfully for order item {order_item.id} to {to_email}"
        )
    except Exception as e:
        logger.error(
            f"Failed to send download link email for order item {order_item.id}: {str(e)}"
        )
        raise
