from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name="dashboard"),
    path('home', views.home, name="home"),
    path('update_admin_info/', views.update_admin_info, name="update_admin_info"),
    path('delete/<int:pk>', views.delete, name="delete"),
    path('viewer/delete/<int:pk>', views.delete_viewer, name="delete_viewer"),
    path('viewer/', views.viewer_dashboard_view, name="viewer_dashboard"),
    path('alerts/confirm/<int:alert_id>/', views.confirm_alert, name="confirm_alert"),
]
