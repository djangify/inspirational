from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = "tools"

urlpatterns = [
    path("", views.tools_home, name="index"),
    path("calming-game/", views.calming_game, name="calming_game"),
    path("tap-to-calm/", views.tap_to_calm, name="tap_to_calm"),
    path("experiment-results/", views.experiment_results, name="experiment_results"),
    path("an-alive-list-builder/", views.alive_list_builder, name="alive_list_builder"),
    # Redirect the old (trademarked) URL to the new one so existing links keep working
    path(
        "live-it-list-builder/",
        RedirectView.as_view(pattern_name="tools:alive_list_builder", permanent=True),
    ),
]
