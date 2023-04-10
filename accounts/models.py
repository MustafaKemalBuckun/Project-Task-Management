from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(max_length=50)
    is_authorized = models.BooleanField(default=False, blank=True)
    photo = models.ImageField(default=None, blank=True, null=True, upload_to='media/')
