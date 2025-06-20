from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import secrets


# Create your models here.

class APIKey(models.Model):
    key = models.CharField(max_length=64, unique=True, editable=False)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    analyst = models.ForeignKey('Analyst', on_delete=models.CASCADE, related_name='api_keys')

    def __str__(self):
        return f"{self.name} ({self.key[:8]}...)"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_hex(32)  # Generate a 64-character hex string
        super().save(*args, **kwargs)


class AnalystManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        if not extra_fields.get('is_active'):
            raise ValueError('Superuser must have is_active=True.')

        return self.create_user(email, password, **extra_fields)


class Analyst(AbstractUser):

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    username = None


    USERNAME_FIELD = 'email'  #Overriding the default django behavior because by default django login using username and password

    REQUIRED_FIELDS = []
    objects = AnalystManager()
