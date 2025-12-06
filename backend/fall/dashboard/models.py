from django.db import models

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

