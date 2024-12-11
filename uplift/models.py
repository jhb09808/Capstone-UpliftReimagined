from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class Volunteer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    signed_waiver = models.BooleanField(default=False)

class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('Hygiene Items', 'Hygiene Items'),
        ('Canned Food', 'Canned Food'),
        ('Seasonal Clothing', 'Seasonal Clothing'),
        ('Basic Supplies', 'Basic Supplies'),
        ('Entertainment', 'Entertainment'),
        ('Others', 'Others'),
    ]

    name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Others')
    notes = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.quantity} ({self.category})"

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)

class Shift(models.Model):
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved')], default='pending')

    def __str__(self):
        return f"{self.description} ({self.start_time} - {self.end_time})"

class VolunteerLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    activity = models.CharField(max_length=255)
    hours = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.activity} on {self.date}"

class ShiftHistory(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    description = models.CharField(max_length=200)
    activity = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']