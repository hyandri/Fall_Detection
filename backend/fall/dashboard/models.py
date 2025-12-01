from django.db import models
from django.conf import settings


class Administrator(models.Model):
    # One admin only; update email and phone number as needed
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)  # optional phone

    def __str__(self):
        return f"Administrator: {self.email}"


class Contact(models.Model):
    name=models.TextField()
    phone_number = models.CharField(max_length=20)  
    email = models.EmailField()
    whatsapp_enabled=models.BooleanField(default=False)
    email_enabled=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.phone_number} | {self.email}"


class ViewerProfile(models.Model):
    """Profile linking viewer users to their setup user"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='viewer_profile',
        help_text='The viewer user account'
    )
    setup_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='viewer_profiles',
        help_text='The user who set up the detection system'
    )
    name = models.CharField(
        max_length=200,
        help_text="Viewer's full name"
    )
    email = models.EmailField(
        help_text="Viewer's email address"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Viewer's phone number (optional)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this viewer profile is active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.email}) - Viewer for {self.setup_user.username}"

    class Meta:
        verbose_name = 'Viewer Profile'
        verbose_name_plural = 'Viewer Profiles'
        unique_together = [['setup_user', 'email']]


class FallAlert(models.Model):
    """Fall detection alerts sent to viewers"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('confirmed', 'Confirmed Fall'),
        ('false_alarm', 'False Alarm'),
    ]
    
    setup_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fall_alerts',
        help_text='The user who set up the detection system'
    )
    viewer = models.ForeignKey(
        ViewerProfile,
        on_delete=models.SET_NULL,
        related_name='alerts',
        null=True,
        blank=True,
        help_text='Viewer assigned to review this alert (null = all viewers)'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When the fall was detected'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current status of the alert'
    )
    confidence = models.FloatField(
        null=True,
        blank=True,
        help_text='Confidence score of the detection'
    )
    consecutive_frames = models.IntegerField(
        default=0,
        help_text='Number of consecutive frames with fall detection'
    )
    snapshot_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Path to the saved snapshot image'
    )
    detection_info = models.TextField(
        blank=True,
        help_text='Additional detection information (JSON format)'
    )
    whatsapp_sent = models.BooleanField(
        default=False,
        help_text='Whether WhatsApp notification was sent'
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='confirmed_alerts',
        null=True,
        blank=True,
        help_text='User who confirmed/rejected this alert'
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the alert was confirmed/rejected'
    )

    def __str__(self):
        viewer_name = self.viewer.name if self.viewer else "All Viewers"
        return f"Alert {self.id} - {self.get_status_display()} - {viewer_name} ({self.timestamp})"

    class Meta:
        verbose_name = 'Fall Alert'
        verbose_name_plural = 'Fall Alerts'
        ordering = ['-timestamp']

