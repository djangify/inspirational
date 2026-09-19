import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


MAILERLITE_API_URL = "https://connect.mailerlite.com/api/subscribers"


def add_subscriber(user):
    """
    Add verified user to MailerLite
    """

    # 1. Must be subscribed
    if not user.profile.is_subscribed:
        return

    # 2. Prevent duplicates
    if user.profile.mailerlite_id:
        return

    headers = {
        "Authorization": f"Bearer {settings.MAILERLITE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "email": user.email,
        "fields": {
            "name": user.first_name or "",
        },
        "groups": [settings.MAILERLITE_GROUP_ID],
        "status": "active",
    }

    try:
        response = requests.post(MAILERLITE_API_URL, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()

        # Store MailerLite ID
        user.profile.mailerlite_id = data.get("data", {}).get("id")
        user.profile.save(update_fields=["mailerlite_id"])

    except requests.RequestException as e:
        logger.error(f"MailerLite sync failed for {user.email}: {e}")


def add_email_subscriber(email, name=""):
    """
    Add a standalone email signup (e.g. the homepage hero form) to the
    Inspirational Guidance group. No site account is involved, so unlike
    add_subscriber() above, status is left unset and MailerLite applies its
    own double opt-in confirmation rather than treating the address as
    already verified.
    """
    headers = {
        "Authorization": f"Bearer {settings.MAILERLITE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "email": email,
        "fields": {"name": name},
        "groups": [settings.MAILERLITE_GROUP_ID],
    }

    try:
        response = requests.post(MAILERLITE_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"MailerLite hero signup failed for {email}: {e}")
        return False
