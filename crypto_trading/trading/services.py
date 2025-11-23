# trading/services.py
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Activo, Portafolio, Operacion
from usuarios.models import UsuarioPersonalizado

class TradingService:
    
    @staticmethod
    def ejecutar_orden(user: UsuarioPersonalizado, symbol: str, trade_type: str, amount: Decimal):
        """
        Ejecuta una orden de compra o venta de manera atómica.
        
        :param user: Instancia del usuario
        :param symbol: Símbolo del activo (ej. 'BTC')
        :param trade_type: 'BUY' o 'SELL'
        :param amount: Cantidad de cripto a operar (no fiat)
        """
        
        # Validaciones iniciales
        if amount <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0.")

        # Iniciamos la transacción atómica
        # Si algo falla dentro de este bloque, la DB regresa al estado original.
        with transaction.atomic():
            # 1. Obtener datos actualizados y BLOQUEAR filas (select_for_update)
            # Esto evita que el usuario gaste el mismo saldo dos veces en milisegundos (Race Condition)
            user = UsuarioPersonalizado.objects.select_for_update().get(pk=user.pk)
            activo = Activo.objects.get(symbol=symbol) # Asumimos que el precio ya está actualizado por la IA/Cron
            
            precio_actual = activo.price_usd
            costo_total = precio_actual * amount

            # 2. Lógica de COMPRA
            if trade_type == 'BUY':
                if user.balance < costo_total:
                    raise ValidationError(f"Saldo insuficiente. Requieres ${costo_total:.2f}, tienes ${user.balance:.2f}")

                # Actualizar saldo
                user.balance -= costo_total
                
                # Actualizar/Crear Portafolio
                portafolio, created = Portafolio.objects.get_or_create(
                    user=user, 
                    asset=activo,
                    defaults={'amount': Decimal('0.0'), 'average_price': Decimal('0.0')}
                )
                
                # Cálculo de Precio Promedio de Compra (Weighted Average Price)
                # Formula: ((CantidadActual * PrecioPromedioActual) + (CantidadNueva * PrecioNuevo)) / CantidadTotal
                total_antiguo_usd = portafolio.amount * portafolio.average_price
                total_nuevo_usd = total_antiguo_usd + costo_total
                nueva_cantidad = portafolio.amount + amount
                
                portafolio.average_price = total_nuevo_usd / nueva_cantidad
                portafolio.amount = nueva_cantidad
                portafolio.save()

            # 3. Lógica de VENTA
            elif trade_type == 'SELL':
                # Buscar portafolio (sin create, debe existir)
                try:
                    portafolio = Portafolio.objects.select_for_update().get(user=user, asset=activo)
                except Portafolio.DoesNotExist:
                    raise ValidationError("No posees este activo para vender.")

                if portafolio.amount < amount:
                    raise ValidationError(f"Activos insuficientes. Tienes {portafolio.amount}, quieres vender {amount}")

                # Actualizar saldo
                user.balance += costo_total
                
                # Actualizar Portafolio
                portafolio.amount -= amount
                # Nota: En venta, el 'average_price' de adquisición no cambia contablemente, solo la cantidad.
                portafolio.save()
                
                # Limpieza opcional: Si queda en 0 o muy cerca de 0 (polvo), ¿borramos?
                if portafolio.amount <= Decimal('0.00000001'):
                    portafolio.delete()

            else:
                raise ValidationError("Tipo de operación no válida.")

            # 4. Guardar cambios de usuario
            user.save()

            # 5. Registrar Historial (Auditoría)
            operacion = Operacion.objects.create(
                user=user,
                asset=activo,
                trade_type=trade_type,
                amount=amount,
                price=precio_actual,
                timestamp=timezone.now()
            )

            return operacion