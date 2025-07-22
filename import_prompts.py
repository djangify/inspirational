import os
import json
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inspirational.settings.local")
django.setup()

from prompt.models import PromptCategory, WritingPrompt, WritingStyle, Tag


def import_prompts():
    # Define your default categories and their slugs
    categories = {
        "Relationships": "relationships",
        "Health & Wellness": "health-wellness",
        "Hobbies": "hobbies",
        "Achievements": "achievements",
        "Self Discovery": "self-discovery",
        "Challenges": "challenges",
        "Love And Heartbreak": "love-heartbreak",
        "Life Experiences": "life-experiences",
        "Family Stories": "family-stories",
        "Childhood Memories": "childhood-memories",
        "Daily Practice": "daily-practice",
        "Mindfulness": "mindfulness",
        "Meditation": "meditation",
        "Confidence Building": "confidence-building",
        "Intentional Living": "intentional-living",
        "Life Purpose": "life-purpose",
    }

    category_objects = {}

    # Create or fetch PromptCategory objects
    for name, slug in categories.items():
        category, created = PromptCategory.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": f"Prompts about {name.lower()}",
                "sub_category": None,  # You can add subcategories later
            },
        )
        category_objects[name] = category
        if created:
            print(f"Created category: {name}")
        else:
            print(f"Found existing category: {name}")

    # Load JSON prompt data
    with open("writing_prompts.json", "r", encoding="utf-8") as file:
        prompts_data = json.load(file)

    count = 0

    for prompt_data in prompts_data:
        if prompt_data["model"] != "prompt.writingprompt":
            continue

        fields = prompt_data["fields"]
        text = fields["text"]
        category_name = fields["category"]

        if category_name not in category_objects:
            print(f"⚠️ Category not found: {category_name}")
            continue

        category = category_objects[category_name]

        # Check for duplicates
        if WritingPrompt.objects.filter(text=text, category=category).exists():
            print(f"⏭️ Skipped duplicate: {text[:50]}...")
            continue

        prompt = WritingPrompt(
            text=text,
            category=category,
            difficulty=fields.get("difficulty", "medium"),
            prompt_type=fields.get("prompt_type", "journal"),
            active=fields.get("active", True),
        )
        prompt.save()

        # Handle WritingStyles (ManyToMany)
        for style_name in fields.get("writing_styles", []):
            style_obj, _ = WritingStyle.objects.get_or_create(name=style_name)
            prompt.writing_styles.add(style_obj)

        # Handle Tags (ManyToMany)
        for tag_name in fields.get("tags", []):
            tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
            prompt.tags.add(tag_obj)

        prompt.save()
        count += 1
        print(f"✅ Added prompt ({count}): {text[:50]}...")

    print(f"\n🎉 Import complete! {count} new prompts added.")


if __name__ == "__main__":
    import_prompts()
