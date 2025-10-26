from django.urls import path
from . import views


# mainapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("contacts/", views.contacts, name="contacts"),
    path("login/", views.loginout, name="login"),  # Make sure this is 'login'
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("send-alert/", views.send_alert, name="send_alert"),
    path("alerts/", views.alerts_list, name="alerts_list"),
    path("detect-fall/", views.detect_fall, name="detect_fall"),
    path("get-alerts/", views.get_alerts, name="get_alerts"),
]