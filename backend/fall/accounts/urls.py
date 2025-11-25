from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.signup, name="signup"),
    path('loginout', views.loginout, name="loginout"),
    path('logout', views.logout, name="logout"),
    path('google/login', views.google_login, name="google_login"),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),

]