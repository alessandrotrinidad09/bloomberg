from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import JSONField
import random

# Create your models here.

class UsuarioPersonalizado(AbstractUser):
    dni = models.CharField(max_length=8, unique=True)
    nombre = models.CharField(max_length=30)
    apellido = models.CharField(max_length=30)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    # Notificaciones
    notif_inicio_sesion = models.BooleanField(default=True, verbose_name="Alerta de inicio de sesión")
    notif_marketing = models.BooleanField(default=False, verbose_name="Correos de marketing")
    
    # Privacidad
    priv_perfil_publico = models.BooleanField(default=False, verbose_name="Perfil público")
    priv_compartir_datos = models.BooleanField(default=True, verbose_name="Compartir datos anónimos")

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
    is_active = models.BooleanField(default=False)

    two_factor_enabled = models.BooleanField(default=False) # Habilitar 2FA
    two_factor_code = models.CharField(max_length=6, blank=True, null=True)

    def generate_two_factor_code(self):
        """Genera un código de 6 dígitos y lo guarda."""
        code = str(random.randint(100000, 999999))
        self.two_factor_code = code
        self.save()
        return code

    def __str__(self):
        return f"{self.username} ({self.nombre} {self.apellido})"
    
    