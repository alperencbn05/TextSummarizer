from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Summary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    original_text = models.TextField()
    summary_text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    bullet_points = models.BooleanField(default=False)
    summary_length = models.CharField(max_length=10, default='medium')
    is_guest = models.BooleanField(default=False)
    guest_email = models.EmailField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

class GuestUsage(models.Model):
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Guest Usage'
        verbose_name_plural = 'Guest Usages'

    def __str__(self):
        return f"{self.ip_address} - {self.timestamp}"
