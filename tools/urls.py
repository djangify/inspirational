from django.urls import path
from . import views

app_name = "tools"

urlpatterns = [
    path("", views.tools_home, name="index"),
    path("calming-game/", views.calming_game, name="calming_game"),
    path("tap-to-calm/", views.tap_to_calm, name="tap_to_calm"),
    path("experiment-results/", views.experiment_results, name="experiment_results"),
    path("live-it-list-builder/", views.live_it_list_builder, name="live_it_list_builder"),
]
