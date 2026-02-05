from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='member')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.IntegerField(null=True)
    joined_date = models.DateField(null=True)