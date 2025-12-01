from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile with user type information"""
    USER_TYPE_CHOICES = [
        ('setup', 'Setup User'),
        ('viewer', 'Viewer User'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='setup',
        help_text='Type of user: setup user manages the system, viewer user monitors alerts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
