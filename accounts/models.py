from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    is_translator = models.BooleanField(default=False)
    is_lawyer = models.BooleanField(default=False)


class ActiveUser(models.Model):
    username = models.CharField(max_length=125)
    is_admin = models.BooleanField(default=False)
    is_translator = models.BooleanField(default=False)
    is_lawyer = models.BooleanField(default=False)