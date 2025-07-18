from decimal import Decimal
from django.conf import settings
from .models import Product


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        """
        product_ids = self.cart.keys()
        # Get the product objects and add them to the cart
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        for product in products:
            # Create a temporary item dict for yielding, don't modify the session cart
            item = cart[str(product.id)].copy()
            item["product"] = product
            item["image_url"] = product.get_image_url()
            item["price"] = Decimal(str(item["price"]))
            item["total_price"] = item["price"] * item["quantity"]
            yield item

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            # Store only JSON serializable data - no Decimal objects
            self.cart[product_id] = {
                "quantity": 0,
                "price": str(product.price),  # Always store as string
            }
        if override_quantity:
            self.cart[product_id]["quantity"] = quantity
        else:
            self.cart[product_id]["quantity"] += quantity
        self.save()

    def save(self):
        # Mark the session as modified but don't reassign the cart
        # The cart should already contain only JSON serializable data
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def get_total_price(self):
        """
        Calculate total price of items in cart.
        """
        return sum(
            Decimal(str(item["price"])) * item["quantity"]
            for item in self.cart.values()
        )

    def clear(self):
        """Remove cart from session"""
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
