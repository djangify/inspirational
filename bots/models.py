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
        default=50,
        help_text="Maximum number of messages a user can send (50 for individual, 150 for bundles)"
    )
    access_days = models.PositiveIntegerField(
        default=60,
        help_text="Number of days access is granted after purchase (60 for individual, 90 for bundles)"
    )
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bot: {self.product.title}"

class BotKnowledge(models.Model):
    """
    A PDF knowledge file attached to a BotProduct.
    Multiple files can be attached (e.g. for toolkits).
    """
    bot_product = models.ForeignKey(
        BotProduct,
        on_delete=models.CASCADE,
        related_name='knowledge_files'
    )
    title = models.CharField(
        max_length=100,
        help_text="e.g. Momentum Your Way Workbook"
    )
    knowledge_file = models.FileField(
        upload_to='bot_knowledge/',
        help_text="PDF file only"
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Order in which files are added to the prompt"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created']

    def __str__(self):
        return f"{self.title} ({self.bot_product.bot_name})"

class BotAccess(models.Model):
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
    bonus_messages = models.PositiveIntegerField(
        default=0,
        help_text="Extra messages granted manually (e.g. top-up purchases)"
    )
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
        return max(0, self.bot_product.message_limit + self.bonus_messages - self.message_count)

    @property
    def days_remaining(self):
        if self.is_expired:
            return 0
        delta = self.access_expires - timezone.now()
        return delta.days

    @property
    def has_access(self):
        return not self.is_expired and self.messages_remaining > 0

class BotConversation(models.Model):
    """
    Persists a user's conversation with a bot across sessions.
    One record per user per bot product.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bot_conversations'
    )
    bot_product = models.ForeignKey(
        BotProduct,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    messages = models.JSONField(
        default=list,
        help_text="Full conversation history as a list of role/content dicts"
    )
    quiz_answers = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stored quiz question and answer pairs"
    )
    saved_goal = models.TextField(
        blank=True,
        help_text="The goal text the user chose to save to the tracker"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'bot_product')
        verbose_name_plural = 'Bot Conversations'

    def __str__(self):
        return f"{self.user.username} - {self.bot_product.bot_name}"

    def message_count(self):
        return len(self.messages)