# remove_bom_final.py
from pathlib import Path

file_path = Path("data.json")
data = file_path.read_bytes()

# Elimina BOM si existe
if data.startswith(b'\xef\xbb\xbf'):
    print("🧽 Se detectó y eliminó el BOM.")
    data = data[3:]
else:
    print("✅ No se detectó BOM, solo se reescribirá el archivo.")

# Guardar una versión totalmente limpia
clean_path = Path("data_final.json")
clean_path.write_bytes(data)

print("✅ Archivo limpio guardado como:", clean_path)
