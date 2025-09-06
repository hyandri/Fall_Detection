from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("send-alert/", views.send_alert, name="send_alert"),
]
