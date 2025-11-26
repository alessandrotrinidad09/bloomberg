import pandas as pd
from django.core.management.base import BaseCommand
from trading.models import Activo, PrecioPrediccion # <--- CAMBIO AQUÍ
from decimal import Decimal

class Command(BaseCommand):
    help = 'Carga PREDICCIONES futuras desde un Excel'

    def add_arguments(self, parser):
        parser.add_argument('archivo_excel', type=str)
        parser.add_argument('simbolo', type=str)

    def handle(self, *args, **kwargs):
        archivo = kwargs['archivo_excel']
        simbolo = kwargs['simbolo']

        try:
            activo = Activo.objects.get(symbol=simbolo)
        except Activo.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'El activo {simbolo} no existe.'))
            return

        self.stdout.write(f"Cargando predicciones para {simbolo}...")

        # Ajusta header y usecols según tu Excel de predicciones
        # Asumo que es idéntico al anterior (Fila 6 cabecera)
        try:
            df = pd.read_excel(archivo, header=5, usecols="A:D")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error leyendo Excel: {e}"))
            return

        df.columns = df.columns.str.strip()
        registros = []
        precio_anterior = None

        for index, row in df.iterrows():
            try:
                fecha = pd.to_datetime(row['Dates']).date()
                close = Decimal(str(row['PX_LAST']))
                low = Decimal(str(row['PX_LOW']))
                high = Decimal(str(row['PX_HIGH']))
                
                # Lógica de Open igual a la anterior
                open_p = precio_anterior if precio_anterior else close
                
                # Validaciones de velas
                if open_p > high: high = open_p
                if close > high: high = close
                if open_p < low: low = open_p
                if close < low: low = close

                obj = PrecioPrediccion(
                    asset=activo,
                    date=fecha,
                    open_price=open_p,
                    high_price=high,
                    low_price=low,
                    close_price=close
                )
                registros.append(obj)
                precio_anterior = close

            except Exception as e:
                continue

        PrecioPrediccion.objects.bulk_create(registros, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'¡ÉXITO! {len(registros)} predicciones cargadas.'))