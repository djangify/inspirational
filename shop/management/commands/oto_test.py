"""
Test the One-Time Offer without Stripe, a staging site, or buying anything.

Examples (run from the project root, or on the VPS inside your venv):

    # See the offer config + whether a user would be shown the offer
    python manage.py oto_test alice

    # Let a user see the offer again (clears their 'seen' stamp)
    python manage.py oto_test alice --reset

    # Pretend the user paid: creates the real order + download, no money taken
    python manage.py oto_test alice --buy

    # Same, and also send the confirmation email
    python manage.py oto_test alice --buy --email
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from shop.models import OneTimeOffer, Order, OrderItem

User = get_user_model()


class Command(BaseCommand):
    help = "Test the one-time offer flow without Stripe (status / --reset / --buy)."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Username or email of the test user.")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Clear the user's oto_seen_at so the offer is shown again.",
        )
        parser.add_argument(
            "--buy",
            action="store_true",
            help="Simulate a completed purchase (creates order + download). No payment is taken.",
        )
        parser.add_argument(
            "--email",
            action="store_true",
            help="With --buy, also send the order confirmation email.",
        )

    def _get_user(self, ident):
        user = (
            User.objects.filter(username=ident).first()
            or User.objects.filter(email__iexact=ident).first()
        )
        if not user:
            raise CommandError(f"No user found matching '{ident}'.")
        return user

    def handle(self, *args, **opts):
        user = self._get_user(opts["username"])
        offer = OneTimeOffer.objects.select_related("product").first()
        if not offer:
            raise CommandError(
                "No One-Time Offer configured yet. Create one in the admin first."
            )

        if opts["reset"]:
            profile = getattr(user, "profile", None)
            if profile is not None:
                profile.oto_seen_at = None
                profile.save(update_fields=["oto_seen_at"])
            self.stdout.write(
                self.style.SUCCESS(f"Reset: {user.username} can see the offer again.")
            )

        if opts["buy"]:
            self._simulate_buy(user, offer, send_email=opts["email"])

        self._print_status(user, offer)

    def _print_status(self, user, offer):
        profile = getattr(user, "profile", None)
        seen = profile.oto_seen_at if profile else None

        self.stdout.write("")
        self.stdout.write("One-Time Offer")
        self.stdout.write(f"  enabled .......... {offer.enabled}")
        self.stdout.write(f"  title ............ {offer.title!r}")
        self.stdout.write(f"  price ............ £{offer.price:.2f}")
        self.stdout.write(f"  file uploaded .... {bool(offer.file)}")
        self.stdout.write(f"  hidden product ... id={offer.product_id}")
        self.stdout.write("")
        self.stdout.write(f"User: {user.username} <{user.email}>")
        self.stdout.write(f"  staff/superuser .. {user.is_staff or user.is_superuser}")
        self.stdout.write(f"  seen offer at .... {seen}")

        eligible = offer.is_eligible_for(user)
        style = self.style.SUCCESS if eligible else self.style.WARNING
        self.stdout.write(style(f"  => shown on next login: {eligible}"))

        if not eligible:
            reasons = []
            if not offer.enabled:
                reasons.append("offer not enabled")
            if user.is_staff or user.is_superuser:
                reasons.append("user is staff/superuser (always excluded)")
            if not offer.file:
                reasons.append("no file uploaded on the offer")
            if seen is not None:
                reasons.append("user already saw it (use --reset)")
            owns = OrderItem.objects.filter(
                order__user=user, product=offer.product, order__status="completed"
            ).exists()
            if owns:
                reasons.append("user already owns it")
            if reasons:
                self.stdout.write("     why not: " + "; ".join(reasons))

    def _simulate_buy(self, user, offer, send_email=False):
        product = offer.product
        if not product:
            raise CommandError(
                "The offer has no file/product yet — upload a file in the admin first."
            )

        pi_id = f"TEST-OTO-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        order = Order.objects.create(
            user=user,
            email=user.email,
            payment_intent_id=pi_id,
            paid=True,
            status="completed",
        )
        item = OrderItem.objects.create(
            order=order,
            product=product,
            price_paid_pence=offer.price_pence,
            quantity=1,
        )
        product.purchase_count += 1
        product.save()

        bundled_count = 0
        for bundled in offer.included_products.all():
            OrderItem.objects.create(
                order=order,
                product=bundled,
                price_paid_pence=0,
                quantity=1,
            )
            bundled.purchase_count += 1
            bundled.save(update_fields=["purchase_count"])
            bundled_count += 1

        profile = getattr(user, "profile", None)
        if profile is not None and profile.oto_seen_at is None:
            profile.oto_seen_at = timezone.now()
            profile.save(update_fields=["oto_seen_at"])

        if send_email:
            try:
                from shop.emails import (
                    send_order_confirmation_email,
                    send_admin_new_order_email,
                )
                send_order_confirmation_email(order)
                send_admin_new_order_email(order)
                self.stdout.write("  confirmation email sent")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  email failed: {e}"))

        self.stdout.write(
            self.style.SUCCESS("Simulated purchase complete — no payment was taken.")
        )
        self.stdout.write(f"  order ........... {order.order_id}")
        self.stdout.write(f"  bundled unlocked  {bundled_count} product(s) + their coaches")
        self.stdout.write(f"  download URL .... {reverse('shop:secure_download', args=[item.id])}")
        self.stdout.write(f"  account page .... {reverse('shop:purchases')}")
