from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_order_confirmation_email(order):
    subject = f"Your Order Confirmation - #{order.id}"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.user.email

    context = {
        "order": order,
        "user": order.user,
        "first_name": order.user.first_name,
        "email": order.user.email,
        "items": order.items.all(),
        "total": order.get_total_cost(),
    }

    html_content = render_to_string("email/order_confirmation.html", context)

    email = EmailMultiAlternatives(subject, "", from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
