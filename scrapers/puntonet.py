import requests
import io
import re
import pandas as pd
from pypdf import PdfReader

def scrapear_puntonet_pdf():
    print(" Iniciando Agente de Documentos (Puntonet)...")
    
    # URL oficial del tarifario 2025
    url = "https://www.puntonet.ec/wp-content/uploads/PUNTONET-2026-NTF-CRP-PROM-001.pdf"

# --- EL DISFRAZ (HEADERS) ---
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.puntonet.ec/"
    }
    
    print(" Descargando archivo PDF...")
    
    try:
        # Usamos los headers para evitar el error 403
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        archivo_pdf = io.BytesIO(response.content)
        print(" ¡Acceso concedido! Archivo descargado en memoria.")
    except Exception as e:
        print(f" Error crítico al descargar: {e}")
        return

    # --- FASE DE LECTURA ---
    try:
        reader = PdfReader(archivo_pdf)
        texto_completo = ""
        
        print(f" Leyendo {len(reader.pages)} páginas...")
        for i, pagina in enumerate(reader.pages):
            texto_extraido = pagina.extract_text()
            if texto_extraido:
                texto_completo += f"\n--- Pagina {i+1} ---\n" + texto_extraido
                
    except Exception as e:
        print(f"Error al leer el PDF: {e}")
        return

    # --- FASE DE MINERÍA (REGEX) ---
    planes_data = []
    lineas = texto_completo.split('\n')
    
    print(" Buscando patrones de precios y megas...")
    
    for linea in lineas:
        linea = linea.strip()
        
        # Filtro: Buscamos líneas con "Mbps" o "Megas"
        if ("mbps" in linea.lower() or "megas" in linea.lower()) and any(char.isdigit() for char in linea):
            
            # 1. Extraer Velocidad
            match_velocidad = re.search(r'(\d+)\s*(Mbps|Megas|megas)', linea, re.IGNORECASE)
            
            # 2. Extraer Precio (Detectamos formatos como 22.40 o 22,40)
            match_precio = re.search(r'(\d+[.,]\d{2})', linea)
            
            if match_velocidad and match_precio:
                precio_detectado = match_precio.group(1).replace(',', '.')
                velocidad_detectada = match_velocidad.group(0)

                # Descartamos falsos positivos (si precio == velocidad)
                if precio_detectado != match_velocidad.group(1):
                     planes_data.append({
                        "Proveedor": "Puntonet",
                        "Velocidad": velocidad_detectada,
                        "Precio": f"${precio_detectado}"
                    })

    # --- RESULTADOS ---
    if planes_data:
        df = pd.DataFrame(planes_data)
        # Eliminamos duplicados
        df = df.drop_duplicates(subset=['Velocidad', 'Precio'])
        
        print(f"\n ¡ÉXITO! Se encontraron {len(df)} planes en el PDF:")
        print(df.to_string(index=False))
        df.to_csv("data/datos_puntonet.csv", index=False)
    else:
        print(" El PDF se descargó, pero no encontré patrones de texto claros.")
        print("Es posible que sea una imagen escaneada.")
        
if __name__ == "__main__":
    scrapear_puntonet_pdf()