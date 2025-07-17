# news/urls.py

from django.urls import path
from . import views

app_name = "news"

urlpatterns = [
    path("", views.news_list, name="list"),
    path("category/<slug:slug>/", views.category_list, name="category"),
    path("<slug:slug>/", views.post_detail, name="detail"),
]
