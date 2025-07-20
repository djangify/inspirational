from django import forms
from django.utils import timezone
from .models_tracker import WritingGoal, WritingSession
from .models import WritingPrompt


class DateInput(forms.DateInput):
    input_type = "date"


class WritingGoalForm(forms.ModelForm):
    """Form for creating and editing writing goals"""

    class Meta:
        model = WritingGoal
        fields = [
            "goal_type",
            "target_value",
            "frequency",
            "start_date",
            "end_date",
            "active",
            "notes",
        ]
        widgets = {
            "start_date": DateInput(),
            "end_date": DateInput(),
            "notes": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Why did you set this goal? What are you working towards?",
                    "class": "resize-y min-h-[80px]",
                }
            ),
            "target_value": forms.NumberInput(attrs={"min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes for styling
        for field_name, field in self.fields.items():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                f"form-control rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 {existing_class}".strip()
            )

        # Set today as min date for start_date
        self.fields["start_date"].widget.attrs["min"] = (
            timezone.now().date().isoformat()
        )

        # Apply specific classes and text based on field
        self.fields["goal_type"].widget.attrs["class"] += " w-full"
        self.fields["target_value"].widget.attrs["class"] += " w-full"
        self.fields["frequency"].widget.attrs["class"] += " w-full"

        # Set placeholders and help texts
        self.fields["target_value"].widget.attrs["placeholder"] = (
            "e.g., 30 minutes, 500 words, etc."
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # If end date is provided, make sure it's after start date
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date must be after start date")

        return cleaned_data


class WritingSessionForm(forms.ModelForm):
    """Form for recording writing sessions"""

    class Meta:
        model = WritingSession
        fields = ["date", "minutes_spent", "word_count", "prompt_used", "mood", "notes"]
        widgets = {
            "date": DateInput(),
            "notes": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "What did you write about? How did it go?",
                    "class": "resize-y min-h-[80px]",
                }
            ),
            "minutes_spent": forms.NumberInput(attrs={"min": 1}),
            "word_count": forms.NumberInput(attrs={"min": 0}),
            "prompt_used": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Paste or type your writing prompt here...",
                    "class": "resize-y min-h-[80px]",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = (
                "form-control rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
            )

        # Apply specific classes and text based on field
        self.fields["date"].widget.attrs["class"] += " w-full"
        self.fields["minutes_spent"].widget.attrs["class"] += " w-full"
        self.fields["word_count"].widget.attrs["class"] += " w-full"
        self.fields["mood"].widget.attrs["class"] += " w-full"
        self.fields["prompt_used"].widget.attrs["class"] += " w-full"

        # Limit prompt_used queryset to active prompts
        self.fields["prompt_used"].queryset = WritingPrompt.objects.filter(active=True)
        self.fields["prompt_used"].empty_label = "No prompt used (Free writing)"

        # Set max date to today
        self.fields["date"].widget.attrs["max"] = timezone.now().date().isoformat()

        # Set placeholders and help texts
        self.fields["minutes_spent"].widget.attrs["placeholder"] = "e.g., 30"
        self.fields["word_count"].widget.attrs["placeholder"] = "e.g., 500 (optional)"

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")

        # Make sure the date is not in the future
        if date and date > timezone.now().date():
            self.add_error("date", "Date cannot be in the future")

        return cleaned_data
