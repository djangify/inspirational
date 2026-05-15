import requests
from django.conf import settings


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
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"MailerLite sync failed for {user.email}: {e}")
