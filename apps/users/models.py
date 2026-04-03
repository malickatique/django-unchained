from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

from common.mixins import TimeStampedModel, UuidModel


class User(AbstractUser, UuidModel, TimeStampedModel):
    # timezone = models.CharField(max_length=50, default='UTC')
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'