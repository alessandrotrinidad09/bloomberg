from django.contrib import admin
from .models import Activo, Portafolio, Operacion
# Register your models here.

#AQUI REGISTRAMOS LOS MODELOS DE LA APP TRADING PARA QUE APAREZCAN EN EL ADMINISTRADOR DE DJANGO
@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'price_usd', 'market_cap', 'volume_24h', 'last_updated')
    search_fields = ('symbol', 'name')

@admin.register(Portafolio)
class PortafolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'amount', 'average_price', 'last_updated')
    search_fields = ('user__username', 'asset__symbol')



@admin.register(Operacion)
class OperacionAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'trade_type', 'amount', 'price', 'timestamp')
    search_fields = ('user__username', 'asset__symbol')
    list_filter = ('trade_type',)