import pandas as pd
from django.core.management.base import BaseCommand
from trading.models import Activo, PrecioHistorico
from decimal import Decimal

class Command(BaseCommand):
    help = 'Carga precios históricos desde un Excel específico (Header en fila 6)'

    def add_arguments(self, parser):
        parser.add_argument('archivo_excel', type=str, help='Ruta al archivo .xlsx')
        parser.add_argument('simbolo', type=str, help='Símbolo del activo (ej. BTC)')

    def handle(self, *args, **kwargs):
        archivo = kwargs['archivo_excel']
        simbolo = kwargs['simbolo']

        # 1. Validar que el activo exista
        try:
            activo = Activo.objects.get(symbol=simbolo)
        except Activo.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'El activo "{simbolo}" no existe en la base de datos. Créalo primero en el Admin.'))
            return

        self.stdout.write(f"Leyendo archivo Excel: {archivo}...")

        try:
            # --- AJUSTE CLAVE AQUÍ ---
            # header=5: Significa que la cabecera está en la fila 6 (índice 0, 1, 2, 3, 4, [5])
            # usecols="A:D": Solo lee las columnas A, B, C y D
            df = pd.read_excel(archivo, header=5, usecols="A:D")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error leyendo el Excel: {e}"))
            return

        # Limpiar espacios en nombres de columnas por si acaso (" PX_LAST" -> "PX_LAST")
        df.columns = df.columns.str.strip()

        self.stdout.write(f"Procesando {len(df)} registros para {simbolo}...")

        registros = []
        precio_anterior = None

        # Iterar y crear objetos
        for index, row in df.iterrows():
            try:
                # Convertir fecha
                fecha = pd.to_datetime(row['Dates']).date()
                
                # Obtener precios y convertir a Decimal para precisión financiera
                close = Decimal(str(row['PX_LAST']))
                low = Decimal(str(row['PX_LOW']))
                high = Decimal(str(row['PX_HIGH']))

                # Lógica para OPEN (Apertura):
                # Como el Excel no tiene Open, usamos el Close del día anterior.
                # Si es el primer dato, asumimos Open = Close (Doji candle) o Open = Low.
                open_p = precio_anterior if precio_anterior else close

                # Validaciones lógicas para gráfico de velas (Evitar velas rotas)
                # El High NUNCA puede ser menor que Open o Close
                if open_p > high: high = open_p
                if close > high: high = close
                # El Low NUNCA puede ser mayor que Open o Close
                if open_p < low: low = open_p
                if close < low: low = close

                obj = PrecioHistorico(
                    asset=activo,
                    date=fecha,
                    open_price=open_p,
                    high_price=high,
                    low_price=low,
                    close_price=close,
                    volume=0 # Tu Excel no tiene volumen, lo dejamos en 0
                )
                registros.append(obj)
                
                # Guardar cierre para la apertura de mañana
                precio_anterior = close

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Fila {index} saltada por error: {e}"))
                continue

        # Guardar en bloque (Bulk Insert)
        if registros:
            # ignore_conflicts=True evita error si intentas subir el mismo día dos veces
            PrecioHistorico.objects.bulk_create(registros, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f'¡ÉXITO! Se cargaron {len(registros)} registros históricos para {simbolo}.'))
        else:
            self.stdout.write(self.style.WARNING('No se encontraron registros válidos para cargar.'))