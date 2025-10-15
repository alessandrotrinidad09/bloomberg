from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class UsuarioPersonalizado(AbstractUser):
    dni = models.CharField(max_length=8, unique=True)
    nombre = models.CharField(max_length=30)
    apellido = models.CharField(max_length=30)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

