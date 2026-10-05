import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BREVO_CONTACTS_URL = "https://api.brevo.com/v3/contacts"
_TIMEOUT = 10


def _config():
    api_key = (getattr(settings, "BREVO_API_KEY", "") or "").strip()
    list_id = getattr(settings, "BREVO_LIST_ID", None)
    return api_key, list_id


def _create_contact(email, name):
    """Create (or update) a Brevo contact on the site's list. Returns the
    response JSON ({} when Brevo answers 204 for an existing contact), or None
    when Brevo is not configured. Raises requests.RequestException on failure."""
    api_key, list_id = _config()
    if not api_key or not list_id:
        logger.warning("Brevo is not configured (BREVO_API_KEY / BREVO_LIST_ID); skipped %s", email)
        return None

    payload = {
        "email": email,
        "attributes": {"FIRSTNAME": name or ""},
        "listIds": [int(list_id)],
        "updateEnabled": True,
    }
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(BREVO_CONTACTS_URL, json=payload, headers=headers, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json() if response.content else {}


def add_subscriber(user):
    """
    Add a verified user who ticked "subscribe" to the Inspirational Guidance
    Brevo list. Never raises: a Brevo problem must not break email verification.
    """
    if not user.profile.is_subscribed:
        return

    if user.profile.mailerlite_id:  # field name kept; now holds the Brevo contact id
        return

    try:
        data = _create_contact(user.email, user.first_name)
        if data and data.get("id"):
            user.profile.mailerlite_id = str(data["id"])
            user.profile.save(update_fields=["mailerlite_id"])
    except requests.RequestException as e:
        logger.error("Brevo sync failed for %s: %s", user.email, e)


CONFIRM_SALT = "inspirational-newsletter-confirm"
CONFIRM_MAX_AGE = 60 * 60 * 24 * 7  # the link works for 7 days


def send_confirmation_email(email, name, confirm_url):
    """Email a confirmation link. The address only joins the list after the link
    is clicked (double opt-in). Returns True when the email was handed to SMTP."""
    from django.core.mail import send_mail

    greeting = f"Hi {name}," if name else "Hello,"
    body = (
        f"{greeting}\n\n"
        "You asked to hear from Inspirational Guidance. Please confirm your email "
        "address by clicking the link below, and I will send you your first email.\n\n"
        f"{confirm_url}\n\n"
        "If you did not ask to join, you can ignore this email and nothing will happen.\n\n"
        "Diane\nInspirational Guidance\n"
    )
    try:
        send_mail(
            "Please confirm your subscription",
            body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:  # noqa: BLE001 - a mail problem must not break the page
        logger.error("Confirmation email failed for %s: %s", email, e)
        return False


def add_email_subscriber(email, name="", request=None):
    """
    Homepage hero form signup, with double opt-in: send a confirmation link now;
    confirm_subscription() adds the address to the Brevo list when it is clicked.
    """
    from django.core import signing
    from django.urls import reverse

    token = signing.dumps({"e": email, "n": name or ""}, salt=CONFIRM_SALT)
    path = reverse("core:confirm_newsletter", args=[token])
    base = (getattr(settings, "SITE_URL", "") or "").rstrip("/")
    if base:
        confirm_url = f"{base}{path}"
    elif request is not None:
        confirm_url = request.build_absolute_uri(path)
    else:
        confirm_url = path
    return send_confirmation_email(email, name, confirm_url)


def confirm_subscription(token):
    """Verify a confirmation token and add the address to the list.
    Returns True when the address is now on the list, False for a bad or expired link."""
    from django.core import signing

    try:
        data = signing.loads(token, salt=CONFIRM_SALT, max_age=CONFIRM_MAX_AGE)
    except signing.BadSignature:
        return False
    try:
        _create_contact(data["e"], data.get("n", ""))
        return True
    except requests.RequestException as e:
        logger.error("Brevo confirm failed for %s: %s", data.get("e"), e)
        return False
