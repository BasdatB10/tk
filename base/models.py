from django.contrib.auth.models import *
from django.db import models

# FAKE USER, DON'T UTILIZE
class SizopiUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email harus diisi')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)
    
class SizopiUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=50)
    nama_depan = models.CharField(max_length=50)
    nama_tengah = models.CharField(max_length=50)
    nama_belakang = models.CharField(max_length=50)
    no_telepon = models.CharField(max_length=15)

    # Fields from PermissionsMixin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = SizopiUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nama_depan', 'nama_belakang', 'no_telepon']

    def __str__(self):
        return self.username