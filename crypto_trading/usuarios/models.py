from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import JSONField

# Create your models here.

class UsuarioPersonalizado(AbstractUser):
    dni = models.CharField(max_length=8, unique=True)
    nombre = models.CharField(max_length=30)
    apellido = models.CharField(max_length=30)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    # Campos adicionales para trading
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    RISK_CHOICES = [
        ('CON', 'Conservador'),
        ('MOD', 'Moderado'),
        ('AGR', 'Agresivo'),
    ]
    risk_profile = models.CharField(max_length=3, choices=RISK_CHOICES, default='MOD')
    preferences = JSONField(blank=True, null=True, default=dict)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.nombre} {self.apellido})"