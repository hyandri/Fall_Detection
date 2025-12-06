from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("send-alert/", views.send_alert, name="send_alert"),
    path("webcam/start/", views.start_webcam, name="start_webcam"),
    path("webcam/stop/", views.stop_webcam, name="stop_webcam"),
    path("webcam/status/", views.get_webcam_status, name="webcam_status"),
    path("frame/", views.get_frame, name="frame"),
    path("detection/enable/", views.enable_detection, name="enable_detection"),
    path("detection/disable/", views.disable_detection, name="disable_detection"),
    path("detection/status/", views.get_detection_status, name="detection_status"),
    path("stream/video/", views.video_stream, name="video_stream"),
    path("stream/raw/", views.video_stream_raw, name="video_stream_raw"),
    path("detection/", views.fall_detection, name="fall_detection"),
    path("alerts/status/", views.get_alert_status, name="alert_status"),
    path("alerts/toggle/", views.toggle_alerts, name="toggle_alerts"),
]