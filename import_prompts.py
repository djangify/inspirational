import os
import json
import django
import environ

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inspirational.settings.production")

# Explicitly load .env.local
env = environ.Env()
environ.Env.read_env(os.path.join(os.path.dirname(__file__), ".env"))

# Setup Django
django.setup()

# This import must stay here - Import models AFTER django.setup()
from prompt.models import PromptCategory, WritingPrompt  # noqa: E402


def import_prompts():
    # Define categories with their slugs
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
    }

    category_objects = {}

    # Create categories if they don't exist and store in dictionary
    for name, slug in categories.items():
        category, created = PromptCategory.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "description": f"Prompts about {name.lower()}"},
        )
        category_objects[name] = category
        if created:
            print(f"Created category: {name}")
        else:
            print(f"Found existing category: {name}")

    # Load JSON data
    with open("writing_prompts.json", "r") as file:
        prompts_data = json.load(file)

    # Process each prompt
    count = 0
    for prompt_data in prompts_data:
        if prompt_data["model"] == "prompt.writingprompt":
            fields = prompt_data["fields"]

            # Get the category object
            category_name = fields["category"]
            if category_name in category_objects:
                category = category_objects[category_name]

                # Check if prompt already exists
                existing = WritingPrompt.objects.filter(
                    text=fields["text"], category=category
                ).exists()

                if not existing:
                    # Create the prompt
                    prompt = WritingPrompt(
                        text=fields["text"],
                        category=category,
                        difficulty=fields["difficulty"],
                        prompt_type=fields["prompt_type"],
                        active=fields.get("active", True),
                    )
                    prompt.save()
                    count += 1
                    print(f"Added prompt ({count}): {fields['text'][:50]}...")
                else:
                    print(f"Skipped existing prompt: {fields['text'][:50]}...")
            else:
                print(f"Category not found: {category_name}")

    print(f"Import completed! Added {count} new prompts.")


if __name__ == "__main__":
    import_prompts()
