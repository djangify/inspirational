# prompt/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Tag, PromptCategory, WritingPrompt
from .serializers import (
    TagSerializer,
    PromptCategorySerializer,
    WritingPromptSerializer,
)
import random
from .models import WritingStyle
from .serializers import WritingStyleSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class PromptCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PromptCategory.objects.all().order_by("name")
    serializer_class = PromptCategorySerializer
    permission_classes = [permissions.AllowAny]


class WritingPromptViewSet(
    viewsets.ReadOnlyModelViewSet
):  # Changed to ReadOnlyModelViewSet
    queryset = WritingPrompt.objects.filter(active=True)
    serializer_class = WritingPromptSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = WritingPrompt.objects.filter(active=True)

        # Get query parameters
        category_slug = self.request.query_params.get("category__slug", None)
        difficulty = self.request.query_params.get("difficulty", None)
        prompt_type = self.request.query_params.get("prompt_type__in", None)
        writing_style = self.request.query_params.get("writing_style", None)
        tags = self.request.query_params.get("tags", None)

        # Apply filters
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        if prompt_type:
            prompt_types = prompt_type.split(",")
            queryset = queryset.filter(prompt_type__in=prompt_types)

        if writing_style:
            queryset = queryset.filter(writing_styles__name__iexact=writing_style)

        if tags:
            tag_list = tags.split(",")
            queryset = queryset.filter(tags__name__in=tag_list).distinct()

        return queryset


class WritingStyleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WritingStyle.objects.all().order_by("name")
    serializer_class = WritingStyleSerializer
    permission_classes = [permissions.AllowAny]


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def random_prompt(request):
    """
    Get a random writing prompt with optional filters,
    tracking previously shown prompts via session to avoid repetition.
    """
    # Get filter parameters
    category_slug = request.query_params.get("category", None)
    difficulty = request.query_params.get("difficulty", None)
    prompt_type = request.query_params.get("type", None)

    # Get current prompt ID to exclude (for "Get Another Prompt")
    current_prompt_id = request.query_params.get("current_id", None)

    # Start with all active prompts
    prompts = WritingPrompt.objects.filter(active=True)

    # Apply filters if provided
    if category_slug and category_slug != "":
        prompts = prompts.filter(category__slug=category_slug)

    if difficulty and difficulty != "":
        prompts = prompts.filter(difficulty=difficulty)

    if prompt_type and prompt_type != "" and prompt_type != "both":
        prompts = prompts.filter(prompt_type__in=[prompt_type, "both"])

    # Exclude current prompt if getting another one
    if current_prompt_id and current_prompt_id.isdigit():
        prompts = prompts.exclude(id=int(current_prompt_id))

    # Initialize the session if it doesn't exist
    if not request.session.session_key:
        request.session.save()

    # Get shown prompts from session
    session_key = f"shown_prompts_{category_slug or 'all'}_{difficulty or 'all'}_{prompt_type or 'all'}"
    shown_prompts = request.session.get(session_key, [])

    # Create a working copy of the queryset before applying session-based filtering
    available_prompts = prompts

    # If we have shown prompts and there are enough prompts to filter
    # Only exclude previously shown prompts if we still have plenty to show
    if shown_prompts and available_prompts.count() > len(shown_prompts) / 2:
        # Create a list of IDs to exclude
        prompts_to_exclude = [id for id in shown_prompts if isinstance(id, int)]

        # Apply the exclusion filter
        available_prompts = available_prompts.exclude(id__in=prompts_to_exclude)

    # Check if we have any prompts after all filtering
    if not available_prompts.exists():
        # If we've excluded all prompts based on session history, reset and use all prompts
        if prompts.exists():
            available_prompts = prompts
            shown_prompts = []  # Reset the shown prompts
            request.session[session_key] = shown_prompts
        else:
            # If there are no prompts with the current filters
            if current_prompt_id:
                # If we're trying to get another prompt but none are available
                response_data = {
                    "message": "You've seen all prompts matching these filters. Try different options.",
                    "no_more_prompts": True,
                }
                return Response(response_data, status=200)
            else:
                # No prompts at all with these filters
                response_data = {
                    "message": "No prompts found with these filters. Try different options.",
                    "no_prompts": True,
                }
                return Response(response_data, status=200)

    # Select a random prompt
    prompt = random.choice(list(available_prompts))

    # Serialize the prompt
    serializer = WritingPromptSerializer(prompt)
    response_data = serializer.data

    # Add a flag indicating this is a valid prompt response
    response_data["is_valid_prompt"] = True

    # Add is_favourite field if user is authenticated
    if request.user.is_authenticated:
        response_data["is_favourite"] = (
            prompt in request.user.profile.favourite_prompts.all()
        )
    else:
        response_data["is_favourite"] = False

    # Add to shown prompts
    if prompt.id not in shown_prompts:
        shown_prompts.append(prompt.id)
        # Limit to last 30 to avoid session bloat
        if len(shown_prompts) > 30:
            shown_prompts = shown_prompts[-30:]
        request.session[session_key] = shown_prompts
        # Save session explicitly to ensure it's stored
        request.session.modified = True

    return Response(response_data)


@login_required
def add_favourite_prompt(request, prompt_id):
    prompt = get_object_or_404(WritingPrompt, id=prompt_id)
    user_profile = request.user.profile

    # Check if the prompt is already in favorites
    is_favourite = prompt in user_profile.favourite_prompts.all()

    # Toggle the favorite status
    if is_favourite:
        user_profile.favourite_prompts.remove(prompt)
        is_favourite = False
        message = "Prompt removed from your profile."
    else:
        user_profile.favourite_prompts.add(prompt)
        is_favourite = True
        message = "Prompt added to your profile!"

    # If the request is AJAX, return a JSON response
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {"status": "success", "is_favourite": is_favourite, "message": message}
        )

    # Otherwise redirect back to referring page
    messages.success(request, message)
    return redirect(request.META.get("HTTP_REFERER", "core:home"))


def journal_prompt_generator(request):
    """
    Dedicated page for journal prompt generator
    """
    return render(request, "prompt/journal_prompt_generator.html")


def prompt_category_view(request, slug):
    category = get_object_or_404(PromptCategory, slug=slug)
    prompts = WritingPrompt.objects.filter(category=category, active=True)
    return render(
        request, "prompt/category.html", {"category": category, "prompts": prompts}
    )
