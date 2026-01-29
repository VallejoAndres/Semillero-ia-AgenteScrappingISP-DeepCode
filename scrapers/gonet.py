from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def scrapear_gonet_texto():
    print(" Iniciando Agente de Texto para Gonet...")
    url = "https://gonet.ec/planes/"
    
    with sync_playwright() as p:
        # Abrimos navegador visible para evitar bloqueos simples
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()
        
        print(f" Navegando a {url}...")
        page.goto(url, timeout=60000)
        
        # Scroll para asegurar que todo cargue 
        page.mouse.wheel(0, 2000)
        time.sleep(3)
        
        # Extraemos el HTML
        html = page.content()
        browser.close()

    print(" HTML capturado. Analizando estructura de datos...")
    soup = BeautifulSoup(html, 'html.parser')
    planes_data = []
    
    # ESTRATEGIA CLÁSICA ROBUSTA: BÚSQUEDA POR BLOQUES
    # Gonet usa Elementor. Los planes suelen estar en columnas.
    # Buscamos todos los DIVs que podrían ser una tarjeta de precios.
    
    # Buscamos divs que tengan la clase 'elementor-widget-wrap' (muy común en su web)
    # O buscamos divs genéricos si no estamos seguros de la clase
    posibles_tarjetas = soup.find_all('div')

    print(f"   -> Analizando {len(posibles_tarjetas)} bloques de la web...")

    for tarjeta in posibles_tarjetas:
        texto = tarjeta.get_text(separator=" ", strip=True)
        
        # Filtros básicos
        if "$" in texto and ("mbps" in texto.lower() or "megas" in texto.lower()) and len(texto) < 400:
            
            # 1. Regex de Precio
            match_precio = re.search(r'\$\s*(\d+)', texto)
            
            # 2. Regex de Velocidad (Mejorado para capturar solo el numero)
            match_velocidad = re.search(r'(\d+)\s*(Mbps|Megas|megas)', texto, re.IGNORECASE)
            
            # 3. Regex de Nombre
            match_nombre = re.search(r'(Plan\s\w+|Go\w+|Fibra\s\w+)', texto, re.IGNORECASE)
            
            if match_precio and match_velocidad:
                precio_num = int(match_precio.group(1)) # Convertimos a entero para ordenar
                velocidad_num = match_velocidad.group(1) # Solo el número (ej: 600)
                
                # Heurística de Nombre: Si encontramos "GoConnect" o similar, lo usamos
                nombre = match_nombre.group(0) if match_nombre else "Plan Fibra Gonet"
            # Guardamos
                planes_data.append({
                    "Proveedor": "Gonet",
                    "Plan": nombre,
                    "Velocidad_Valor": velocidad_num, # Guardamos solo el numero para limpiar
                    "Precio_Valor": precio_num,       # Guardamos solo el numero para limpiar
                    "Velocidad_Final": f"{velocidad_num} Mbps", # Formato bonito
                    "Precio_Final": f"${precio_num}"            # Formato bonito
                })

        # LIMPIEZA FINAL
    if planes_data:
        df = pd.DataFrame(planes_data)
        
        # 1. Ordenamos por Precio (del más barato al más caro)
        # Esto ayuda a que, si hay duplicados, queden juntos
        df = df.sort_values(by=['Precio_Valor', 'Plan'])
        
        # 2. Eliminamos duplicados basándonos en PRECIO y VELOCIDAD
        # (Así "600 MEGAS $16" y "600 megas $16" se vuelven uno solo)
        df = df.drop_duplicates(subset=['Velocidad_Valor', 'Precio_Valor'], keep='first')
        
        # 3. Seleccionamos solo las columnas bonitas para el CSV
        df_final = df[['Proveedor', 'Plan', 'Velocidad_Final', 'Precio_Final']]
        
        print(f"\n ¡ÉXITO! Lista depurada ({len(df_final)} planes únicos):")
        print(df_final.to_string(index=False))
        
        df_final.to_csv("data/datos_gonet.csv", index=False)
    else:
        print(" No se encontraron planes.")

if __name__ == "__main__":
    scrapear_gonet_texto()