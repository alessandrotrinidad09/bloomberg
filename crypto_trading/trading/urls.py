# trading/urls.py
from django.urls import path
from . import views

app_name = 'trading'  # <--- IMPORTANTE: Define el namespace

urlpatterns = [
    # Ruta para la vista de operaciones (GET para ver el form, POST para operar)
    path('operar/', views.trade_view, name='trade_view'),
    path('inversiones/', views.portfolio_view, name='portfolio_view'),
    path('monedas/', views.monedas_view, name='monedas'),

    path('analisis/<str:symbol>/', views.analisis_view, name='analisis')
]