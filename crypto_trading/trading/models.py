from django.db import models
from django.conf import settings

# Create your models here.

#AQUI SE CREA TODOS LOS MODELOS DE LA APP TRADING

# MODELO PARA GUARDAR INFORMACION DE LOS ACTIVOS CRYPTO
class Activo(models.Model):
    symbol = models.CharField(max_length=10, unique=True) 
    name = models.CharField(max_length=50)  
    price_usd = models.DecimalField(max_digits=20, decimal_places=8, default=0.0)
    market_cap = models.DecimalField(max_digits=25, decimal_places=2, blank=True, null=True)
    volume_24h = models.DecimalField(max_digits=25, decimal_places=2, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.name}"
    

# MODELO PARA GUARDAR EL PORTAFOLIO DE CADA USUARIO
class Portafolio(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portafolio'
    )
    asset = models.ForeignKey(
        'Activo',
        on_delete=models.CASCADE,
        related_name='portafolio_entries'
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0.0,
        help_text="Cantidad de la criptomoneda que posee el usuario"
    )
    average_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=0.0,
        help_text="Precio promedio al que se adquirió el activo"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'asset')  # Evita duplicados
        verbose_name = "Portafolio"
        verbose_name_plural = "Portafolios"

    def __str__(self):
        return f"{self.user.username} - {self.asset.symbol}: {self.amount}"

# MODELO PARA GUARDAR TRANSACCIONES (COMPRAS/VENTAS)
from django.utils import timezone

class Operacion(models.Model):
    TRADE_CHOICES = [
        ('BUY', 'Compra'),
        ('SELL', 'Venta'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='operaciones'
    )
    asset = models.ForeignKey(
        'Activo',
        on_delete=models.CASCADE,
        related_name='operaciones'
    )
    trade_type = models.CharField(
        max_length=4,
        choices=TRADE_CHOICES
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=8
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Precio por unidad en USD al momento de la operación"
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.trade_type} {self.amount} {self.asset.symbol} a {self.price}"
