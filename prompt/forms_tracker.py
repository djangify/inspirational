from django import forms
from django.utils import timezone
from .models_tracker import WritingGoal, WritingSession


class DateInput(forms.DateInput):
    input_type = "date"


class WritingGoalForm(forms.ModelForm):
    """Form for creating and editing writing goals"""

    class Meta:
        model = WritingGoal
        fields = [
            "goal_type",
            "goal_label",
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
        self.fields["goal_label"].widget.attrs["class"] += " w-full"
        self.fields["goal_label"].widget.attrs["placeholder"] = (
            "Optional custom label for this goal"
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
    """Form for recording writing sessions (per-goal, required)."""

    class Meta:
        model = WritingSession
        fields = [
            "goal",
            "date",
            "minutes_spent",
            "word_count",
            "prompt_used",
            "mood",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "minutes_spent": forms.NumberInput(attrs={"min": 1}),
            "word_count": forms.NumberInput(attrs={"min": 0}),
            "prompt_used": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "What did you accomplish during this session?",
                    "class": "resize-y min-h-[100px]",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "What did you write about? How did it go?",
                    "class": "resize-y min-h-[80px]",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Styling
        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                "form-control rounded-md border-gray-300 shadow-sm "
                "focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 "
                + existing
            )
        for name in [
            "goal",
            "date",
            "minutes_spent",
            "word_count",
            "mood",
            "prompt_used",
        ]:
            self.fields[name].widget.attrs["class"] += " w-full"

        # Enforce goal selection and limit to the user’s active goals
        self.fields["goal"].required = True
        # If goal is pre-selected (e.g., editing), check its type
        goal = self.initial.get("goal") or self.data.get("goal")
        if goal and isinstance(goal, WritingGoal):
            goal_type = goal.goal_type
        else:
            try:
                goal_instance = WritingGoal.objects.get(id=goal)
                goal_type = goal_instance.goal_type
            except (TypeError, ValueError, WritingGoal.DoesNotExist):
                goal_type = None

        # Conditionally hide or require minutes
        if goal_type == "sessions":
            self.fields["minutes_spent"].required = False
            self.fields["minutes_spent"].widget.attrs["disabled"] = "disabled"
            self.fields["minutes_spent"].widget.attrs["placeholder"] = (
                "Not required for this goal type"
            )
        else:
            self.fields["minutes_spent"].required = True
            self.fields["minutes_spent"].widget.attrs.pop("disabled", None)

        if user is not None:
            self.fields["goal"].queryset = WritingGoal.objects.filter(
                user=user, active=True
            )

        # Disallow future dates
        self.fields["date"].widget.attrs["max"] = timezone.now().date().isoformat()

        # Placeholders
        self.fields["minutes_spent"].widget.attrs["placeholder"] = "e.g., 30"
        self.fields["word_count"].widget.attrs["placeholder"] = "e.g., 500 (optional)"

        # Optional: field order for better UX
        self.order_fields(
            [
                "goal",
                "date",
                "minutes_spent",
                "word_count",
                "mood",
                "prompt_used",
                "notes",
            ]
        )

    def clean(self):
        cleaned = super().clean()
        date = cleaned.get("date")
        goal = cleaned.get("goal")
        minutes_spent = cleaned.get("minutes_spent")

        if date and date > timezone.now().date():
            self.add_error("date", "Date cannot be in the future")

        if goal:
            if goal.goal_type == "time" and not minutes_spent:
                self.add_error(
                    "minutes_spent", "Please enter minutes spent for this goal."
                )
            elif goal.goal_type == "sessions":
                cleaned["minutes_spent"] = (
                    None  # Explicitly clear minutes for session-based goals
                )

        return cleaned

    def clean_goal(self):
        goal = self.cleaned_data.get("goal")
        if not goal:
            raise forms.ValidationError(
                "Please select which goal this session belongs to."
            )
        return goal
