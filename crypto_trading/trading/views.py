# trading/views.py
import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from .services import TradingService
from django.core.exceptions import ValidationError
from .models import Activo, Portafolio, Operacion, PrecioHistorico, PrecioPrediccion
from django.shortcuts import get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
import json

@login_required
def trade_view(request):
    activos = Activo.objects.all() # Para llenar el <select> del HTML
    
    # 2. Obtener el portafolio del usuario y convertirlo en un diccionario
    # Formato: {'BTC': 0.5, 'ETH': 10.0, ...}
    portfolio_dict = {
        item.asset.symbol: item.amount 
        for item in Portafolio.objects.filter(user=request.user)
    }

    # 3. "Inyectar" la cantidad poseída en cada objeto activo temporalmente
    for activo in activos:
        # Si el símbolo está en el diccionario, usa ese valor, si no, 0
        activo.held_amount = portfolio_dict.get(activo.symbol, 0)

    if request.method == 'POST':
        symbol = request.POST.get('asset_symbol')
        trade_type = request.POST.get('trade_type') # 'BUY' o 'SELL'
        amount_str = request.POST.get('amount')

        try:
            amount = Decimal(amount_str)
            
            # LLAMADA AL SERVICIO
            operacion = TradingService.ejecutar_orden(
                user=request.user,
                symbol=symbol,
                trade_type=trade_type,
                amount=amount
            )
            
            messages.success(request, f"Operación exitosa: {trade_type} {amount} {symbol}")
            return redirect('inicio') # O a donde quieras redirigir

        except (ValidationError, InvalidOperation) as e:
            # Capturamos errores de lógica de negocio (Saldo insuficiente, etc)
            messages.error(request, str(e))
        except Exception as e:
            # Capturamos errores inesperados
            messages.error(request, "Ocurrió un error inesperado procesando la orden.")
    
    return render(request, 'trading/trade_form.html', {'activos': activos})


login_required
def portfolio_view(request):
    # 1. FILTRAR POR EL USUARIO ACTUAL (request.user)
    # Si los datos en el admin no son de este usuario, saldrá vacío.
    portfolio_items = Portafolio.objects.filter(user=request.user).select_related('asset')
    historial = Operacion.objects.filter(user=request.user).order_by('-timestamp')

    # --- DEBUGGING (Verás esto en tu terminal negra donde corre el servidor) ---
    print(f"Usuario actual: {request.user}")
    print(f"Items en portafolio encontrados: {portfolio_items.count()}")
    print(f"Operaciones encontradas: {historial.count()}")
    # -------------------------------------------------------------------------

    # 2. Lógica de cálculos (resumida para verificar)
    total_valor_actual = Decimal('0.00')
    total_invertido = Decimal('0.00')
    mejor_inversion = None
    mejor_roi = Decimal('-9999.00')
    
    items_procesados = []

    for item in portfolio_items:
        # Precios
        valor_actual = item.amount * item.asset.price_usd
        costo_base = item.amount * item.average_price
        ganancia_usd = valor_actual - costo_base
        
        # Evitar división por cero
        if costo_base > 0:
            roi_porcentaje = ((valor_actual - costo_base) / costo_base * 100)
        else:
            roi_porcentaje = 0
            
        total_valor_actual += valor_actual
        total_invertido += costo_base

        if roi_porcentaje > mejor_roi:
            mejor_roi = roi_porcentaje
            mejor_inversion = {'symbol': item.asset.symbol, 'roi': roi_porcentaje}
        # Empaquetar datos para el HTML
        items_procesados.append({
            'asset': item.asset,
            'amount': item.amount,
            'avg_price': item.average_price,
            'current_value': valor_actual,
            'ganancia': ganancia_usd,
            'roi': roi_porcentaje,
            'is_positive': ganancia_usd >= 0
        })

    ganancia_total = total_valor_actual - total_invertido
    if total_invertido > 0:
        roi_total = (ganancia_total / total_invertido * 100)
    else:
        roi_total = 0

    # 3. EL CONTEXTO (Esto es lo que lee tu HTML)
    context = {
        'portfolio': items_procesados,  # Tu HTML busca "portfolio"
        'historial': historial,         # Tu HTML busca "historial"
        'total_valor': total_valor_actual,
        'total_invertido': total_invertido,
        'ganancia_total': ganancia_total,
        'roi_total': roi_total,
        'mejor_inversion': mejor_inversion
    }

    return render(request, 'trading/inversiones.html', context)


def monedas_view(request):
    # 1. Obtener todos los activos de la BD
    activos_db = Activo.objects.all().order_by('-market_cap')
    
    activos_procesados = []
    
    # 2. Enriquecer los datos para el diseño (Simulación temporal para UI)
    for activo in activos_db:
        # Simular cambio 24h (entre -5% y +5%)
        # NOTA: En el futuro esto vendrá de la API real o la IA
        cambio_24h = round(random.uniform(-5.0, 5.0), 2)
        tendencia = 'alcista' if cambio_24h >= 0 else 'bajista'
        
        # Simular recomendación IA
        recomendacion = "MANTENER"
        confianza = random.randint(60, 95)
        if cambio_24h > 2:
            recomendacion = "COMPRAR"
        elif cambio_24h < -2:
            recomendacion = "VENDER"
            
        # Asignar un color para el icono basado en el símbolo (hash simple)
        colors = ['bg-orange-500', 'bg-blue-500', 'bg-purple-500', 'bg-yellow-500', 'bg-green-500', 'bg-red-500', 'bg-indigo-500']
        color_icon = colors[len(activo.symbol) % len(colors)]

        # Creamos un diccionario con todo lo necesario para el template
        activos_procesados.append({
            'obj': activo,
            'cambio_24h': cambio_24h,
            'tendencia': tendencia,
            'recomendacion': recomendacion,
            'confianza': confianza,
            'color_icon': color_icon
        })

    return render(request, 'trading/monedas.html', {'activos': activos_procesados})



def analisis_view(request, symbol):
    activo = get_object_or_404(Activo, symbol=symbol)
    
    # 1. Obtener Histórico
    historico = PrecioHistorico.objects.filter(asset=activo).order_by('date')
    chart_data = []
    for h in historico:
        chart_data.append({
            'x': h.date.strftime('%Y-%m-%d'),
            'y': [float(h.open_price), float(h.high_price), float(h.low_price), float(h.close_price)]
        })

    # 2. Obtener Predicciones (NUEVO)
    predicciones = PrecioPrediccion.objects.filter(asset=activo).order_by('date')
    prediction_data = []
    for p in predicciones:
        prediction_data.append({
            'x': p.date.strftime('%Y-%m-%d'),
            'y': [float(p.open_price), float(p.high_price), float(p.low_price), float(p.close_price)]
        })
    
    context = {
        'activo': activo,
        'chart_data': chart_data,          # Histórico
        'prediction_data': prediction_data # Predicciones
    }
    return render(request, 'trading/analisis.html', context)