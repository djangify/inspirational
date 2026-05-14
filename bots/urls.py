# bots/urls.py
from django.urls import path
from . import views

app_name = 'bots'

urlpatterns = [
    path('<slug:product_slug>/', views.bot_chat, name='chat'),
    path('<slug:product_slug>/message/', views.bot_message, name='message'),
    path('<slug:product_slug>/quiz-answers/', views.save_quiz_answers, name='quiz_answers'),
    path('<slug:product_slug>/save-goal/', views.save_goal, name='save_goal'),
    path('<slug:product_slug>/pdf/', views.download_pdf, name='pdf'),
]