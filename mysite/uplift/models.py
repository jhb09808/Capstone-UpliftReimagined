from django.db import models
from django.contrib.auth.models import AbstractUser

class Volunteer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    signed_waiver = models.BooleanField(default=False)

class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
