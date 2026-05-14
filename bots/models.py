# bots/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class BotProduct(models.Model):
    """
    Links a shop Product to a bot configuration.
    One BotProduct per Product that has a bot.
    """
    product = models.OneToOneField(
        'shop.Product',
        on_delete=models.CASCADE,
        related_name='bot'
    )
    bot_name = models.CharField(max_length=100)
    welcome_message = models.TextField(
        help_text="The first message the bot sends when the chat opens"
    )
    system_prompt = models.TextField(
        help_text="The full system prompt that defines the bot's knowledge and behaviour"
    )
    message_limit = models.PositiveIntegerField(
        default=200,
        help_text="Maximum number of messages a user can send"
    )
    access_days = models.PositiveIntegerField(
        default=60,
        help_text="Number of days access is granted after purchase"
    )
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bot: {self.product.title}"


class BotAccess(models.Model):
    """
    Tracks a specific user's access to a specific bot.
    Created when a user first accesses a bot they've purchased.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bot_accesses'
    )
    bot_product = models.ForeignKey(
        BotProduct,
        on_delete=models.CASCADE,
        related_name='accesses'
    )
    message_count = models.PositiveIntegerField(default=0)
    access_expires = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'bot_product')
        verbose_name_plural = 'Bot Accesses'

    def __str__(self):
        return f"{self.user.username} - {self.bot_product.bot_name}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.access_expires:
            self.access_expires = timezone.now() + timedelta(
                days=self.bot_product.access_days
            )
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.access_expires

    @property
    def messages_remaining(self):
        return max(0, self.bot_product.message_limit - self.message_count)

    @property
    def days_remaining(self):
        if self.is_expired:
            return 0
        delta = self.access_expires - timezone.now()
        return delta.days

    @property
    def has_access(self):
        return not self.is_expired and self.messages_remaining > 0