# prompt/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_tracker

app_name = "prompt"

router = DefaultRouter()
router.register(r"tags", views.TagViewSet)
router.register(r"categories", views.PromptCategoryViewSet)
router.register(r"prompts", views.WritingPromptViewSet)
router.register(r"writing-styles", views.WritingStyleViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/random-prompt/", views.random_prompt, name="random-prompt"),
    path("category/<slug:slug>/", views.prompt_category_view, name="category"),
    # Prompt Generator dedicated page
    path(
        "journal-prompt-generator/",
        views.journal_prompt_generator,
        name="journal_prompt_generator",
    ),
    # Writing tracker URLs
    path("writing-progress/", views_tracker.writing_progress, name="writing_progress"),
    path("sessions/", views_tracker.session_list, name="session_list"),
    path("stats/", views_tracker.stats_view, name="stats"),
    # Goal management
    path("add-goal/", views_tracker.add_goal, name="add_goal"),
    path("edit-goal/<int:goal_id>/", views_tracker.edit_goal, name="edit_goal"),
    path("delete-goal/<int:goal_id>/", views_tracker.delete_goal, name="delete_goal"),
    path(
        "toggle-goal/<int:goal_id>/",
        views_tracker.toggle_goal_active,
        name="toggle_goal",
    ),
    # Session management
    path(
        "edit-session/<int:session_id>/",
        views_tracker.edit_session,
        name="edit_session",
    ),
    path(
        "delete-session/<int:session_id>/",
        views_tracker.delete_session,
        name="delete_session",
    ),
]
