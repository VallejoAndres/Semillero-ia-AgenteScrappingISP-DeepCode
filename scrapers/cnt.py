from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def scrapear_cnt_unificado():
    print(" Iniciando Scraper Maestro Unificado para CNT (5 Enlaces)...")
    
    objetivos = [
        {"nombre": "Fibra GO", "url": "https://cnt.com.ec/productos/planes-internet/fibra-optica-go"},
        {"nombre": "Servidor Público", "url": "https://cnt.com.ec/productos/planes-internet/plan-internet-servidor-publico"},
        {"nombre": "Plan Conectados", "url": "https://cnt.com.ec/productos/planes-internet/plan-conectados-iftf"},
        {"nombre": "4 Play (Combos)", "url": "https://cnt.com.ec/productos/planes-internet/4-play"},
        {"nombre": "Otros Planes", "url": "https://cnt.com.ec/productos/planes-internet/internet-otros-planes"}
    ]
    
    resultados = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        
        for objetivo in objetivos:
            print(f"\n Navegando a: {objetivo['nombre']}...")
            try:
                page.goto(objetivo['url'], timeout=60000)
                
                # Scroll generoso para cargar todo
                print("    Scrolleando...")
                page.mouse.wheel(0, 1500)
                time.sleep(4)
                
                # Capturamos HTML y Texto
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                planes_encontrados = 0
                
                # --- INTENTO 1: ESTRATEGIA ESTRUCTURADA (<ARTICLE>) ---
                # Esta es la mejor para Fibra GO, Conectados, 4Play
                tarjetas = soup.find_all('article')
                
                if tarjetas:
                    print(f"   Estrategia HTML: Analizando {len(tarjetas)} tarjetas <article>...")
                    for tarjeta in tarjetas:
                        texto = tarjeta.get_text(separator=" ", strip=True)
                        
                        # Filtros estándar
                        if len(texto) < 500 and ("$" in texto or "USD" in texto):
                            match_vel = re.search(r'(\d+)\s*(Mbps|Megas|Gbps)', texto, re.IGNORECASE)
                            match_precio = re.search(r'[\$|USD]\s*(\d+[.,]?\d*)', texto, re.IGNORECASE)
                            
                            if match_vel and match_precio:
                                precio_limpio = match_precio.group(1).replace(',', '.')
                                nombre_sucio = texto.split()[:6] # Tomamos un poco más de contexto
                                nombre_plan = " ".join(nombre_sucio)
                                
                                datos = {
                                    "Proveedor": "CNT",
                                    "Categoría": objetivo['nombre'],
                                    "Plan Detectado": nombre_plan,
                                    "Velocidad": match_vel.group(0),
                                    "Precio": f"${precio_limpio}",
                                    "Método": "HTML Article"
                                }
                                if datos not in resultados:
                                    resultados.append(datos)
                                    planes_encontrados += 1
                
                # --- INTENTO 2: ESTRATEGIA DE RESCATE (TEXTO PLANO) ---
                # Se activa SOLO si el Intento 1 falló (ej: Servidor Público, Adulto Mayor)
                if planes_encontrados == 0:
                    print("   Estrategia Rescate: No vi artículos, escaneando texto visible...")
                    texto_visible = page.locator("body").inner_text()
                    lineas = texto_visible.split('\n')
                    
                    for linea in lineas:
                        linea = linea.strip()
                        # Filtro relajado para casos especiales
                        if ("$" in linea or "USD" in linea) and 5 < len(linea) < 150:
                            
                            # Buscamos precio obligatoriamente
                            match_precio = re.search(r'[\$|USD]\s*(\d+[.,]?\d*)', linea)
                            
                            if match_precio:
                                # Buscamos velocidad, si no hay, ponemos "Consultar Web"
                                match_vel = re.search(r'(\d+)\s*(Mbps|Megas|Gbps)', linea, re.IGNORECASE)
                                velocidad = match_vel.group(0) if match_vel else "No especificada (Ver Web)"
                                
                                # Si es Servidor Público o Adulto Mayor, guardamos la línea
                                precio_limpio = match_precio.group(1).replace(',', '.')
                                
                                datos = {
                                    "Proveedor": "CNT",
                                    "Categoría": objetivo['nombre'],
                                    "Plan Detectado": linea, # Guardamos la línea entera para contexto
                                    "Velocidad": velocidad,
                                    "Precio": f"${precio_limpio}",
                                    "Método": "Texto Rescate"
                                }
                                if datos not in resultados:
                                    resultados.append(datos)
                                    planes_encontrados += 1
                
                print(f"    Total extraído en esta sección: {planes_encontrados}")

            except Exception as e:
                print(f"    Error en {objetivo['nombre']}: {e}")
        
        browser.close()

    # --- RESULTADOS FINALES ---
    if resultados:
        df = pd.DataFrame(resultados)
        
        # Limpieza final
        df = df.drop_duplicates(subset=['Categoría', 'Precio', 'Velocidad'])
        df = df.sort_values(by=['Categoría', 'Precio'])
        
        print("\n --- INVENTARIO MAESTRO CNT ---")
        # Mostramos columnas clave
        print(df[['Categoría', 'Plan Detectado', 'Velocidad', 'Precio']].to_string(index=False))
        
        df.to_csv("data/datos_cnt_completo.csv", index=False)
        print("\n Guardado en 'datos_cnt.csv'")
    else:
        print("\n No se encontró nada. CNT ha cambiado radicalmente su web.")

if __name__ == "__main__":
    scrapear_cnt_unificado()