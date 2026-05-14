# bots/urls.py
from django.urls import path
from . import views

app_name = 'bots'

urlpatterns = [
    path('<slug:product_slug>/', views.bot_chat, name='chat'),
    path('<slug:product_slug>/message/', views.bot_message, name='message'),
]