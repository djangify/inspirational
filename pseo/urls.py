# pseo/urls.py
from django.urls import path
from . import views

app_name = "pseo"

urlpatterns = [
    path("discover/<slug:slug>/", views.programmatic_page_detail, name="detail"),
]
