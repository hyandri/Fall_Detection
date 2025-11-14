from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.signup, name="signup"),
    path('loginout', views.loginout, name="loginout"),
    path('logout', views.logout, name="logout"),
]