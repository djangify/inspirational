# prompt/models.py
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class PromptCategory(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("prompt:category", kwargs={"slug": self.slug})

    class Meta:
        verbose_name_plural = "Prompt categories"
        ordering = ["name"]


class WritingPrompt(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy (5-10 minutes)"),
        ("medium", "Medium (15-20 minutes)"),
        ("deep", "Deep (30+ minutes)"),
    ]

    TYPE_CHOICES = [
        ("journal", "Journal Entry"),
        ("memoir", "Memoir/Memory"),
        ("both", "Both"),
    ]

    text = models.TextField()
    category = models.ForeignKey(
        PromptCategory, on_delete=models.CASCADE, related_name="prompts"
    )
    difficulty = models.CharField(
        max_length=15, choices=DIFFICULTY_CHOICES, default="medium"
    )
    prompt_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default="both")
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="prompts")

    def __str__(self):
        return self.text[:50] + ("..." if len(self.text) > 50 else "")

    def get_difficulty_display(self):
        difficulty_map = {
            "easy": "Quick (5-10 minutes)",
            "medium": "Medium (15-20 minutes)",
            "deep": "Deep (30+ minutes)",
        }
        return difficulty_map.get(self.difficulty, "Medium (15-20 minutes)")
