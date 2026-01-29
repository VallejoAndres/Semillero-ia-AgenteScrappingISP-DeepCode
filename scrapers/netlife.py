import time
import os
import sys
import json
import pandas as pd
import google.generativeai as genai
from playwright.sync_api import sync_playwright
from PIL import Image

# --- BLOQUE DE CONEXIÓN CON LA API KEY ---
# Truco para importar desde la carpeta superior (donde está config.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from config import API_KEY # Importamos la variable del archivo config.py
    genai.configure(api_key=API_KEY)
except ImportError:
    print("❌ ERROR CRÍTICO: No se encontró 'config.py' o la variable API_KEY.")
    print("Asegúrate de crear el archivo config.py en la carpeta raíz con tu clave.")
    sys.exit(1)
# -----------------------------------------

def agente_netlife_tab_clicker():
    print(" Iniciando Agente Interactivo para NETLIFE (Navegación por Pestañas)...")
    
    # TUS ENLACES DESCUBIERTOS
    objetivos = [
        {"nombre": "Hogar", "url": "https://netlife.ec/planes-hogar/"},
        {"nombre": "Pyme",  "url": "https://netlife.ec/planes-pyme/"}
    ]
    
    imagenes_capturadas = []
    
    with sync_playwright() as p:
        # Modo Visible (Headless=False) para evitar bloqueos y ver qué pasa
        browser = p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        # Viewport alto para intentar capturar más planes de una sola vez
        context = browser.new_context(viewport={"width": 1366, "height": 900})
        page = context.new_page()
        
        for obj in objetivos:
            print(f"\n Navegando a: Netlife {obj['nombre']}...")
            try:
                page.goto(obj['url'], timeout=60000)
                
                # Espera inicial para carga y popups
                print("    Esperando carga completa...")
                time.sleep(6) 
                
                # --- LIMPIEZA DE POPUPS ---
                print("    Intentando cerrar popups (Escape + Clic)...")
                page.keyboard.press("Escape")
                time.sleep(1)
                try:
                    page.mouse.click(50, 50) # Clic en esquina por si acaso
                except:
                    pass
                
                # --- FOTO 1: PARTE SUPERIOR (Planes 1, 2, 3) ---
                # Hacemos un pequeño ajuste de scroll para saltar el menú de navegación
                page.mouse.wheel(0, 300) 
                time.sleep(2)
                
                img_top = f"netlife_{obj['nombre']}_TOP.png"
                page.screenshot(path=img_top)
                print(f"    Foto Superior: {img_top}")
                imagenes_capturadas.append(img_top)
                
                # --- FOTO 2: PARTE INFERIOR (Plan 4 y detalles) ---
                print("    Bajando para buscar el 4to plan oculto...")
                page.mouse.wheel(0, 500) # Bajamos 500px más
                time.sleep(3) # Esperamos que se estabilice la imagen
                
                img_bottom = f"netlife_{obj['nombre']}_BOTTOM.png"
                page.screenshot(path=img_bottom)
                print(f"    Foto Inferior: {img_bottom}")
                imagenes_capturadas.append(img_bottom)
                
            except Exception as e:
                print(f"    Error en {obj['nombre']}: {e}")
        
        browser.close()

    # --- FASE IA (GEMINI) ---
    if imagenes_capturadas:
        print(f"\n Analizando {len(imagenes_capturadas)} capturas con Gemini...")
        
        try:
            modelo = genai.GenerativeModel('gemini-2.5-flash')
            lista_imgs = [Image.open(img) for img in imagenes_capturadas]
            
            prompt = """
            Eres un experto en telecomunicaciones. Analiza estas capturas de NETLIFE (Hogar y Pyme).
            
            TU MISIÓN:
            1. Extrae TODOS los planes de internet.
            2. Busca el 4to plan que suele estar escondido a la derecha o abajo.
            3. Elimina duplicados visuales.
            4. Extrae:
               - Categoria (Hogar o Pyme)
               - Plan (Nombre del plan)
               - Velocidad (ej: 300 Mbps)
               - Precio (ej: $24.90 incl imp)
               - Detalles
            
            Responde SOLO JSON válido:
            [
                {"Categoria": "...", "Plan": "...", "Velocidad": "...", "Precio": "...", "Detalles": "..."}
            ]
            """
            
            respuesta = modelo.generate_content([prompt] + lista_imgs)
            texto_limpio = respuesta.text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(texto_limpio)
            
            if data:
                df = pd.DataFrame(data)
                df["Proveedor"] = "Netlife"
                
                # Ordenar columnas
                cols = ["Proveedor", "Categoria", "Plan", "Velocidad", "Precio"]
                # Asegurar que existan
                for col in cols:
                    if col not in df.columns: df[col] = ""
                df = df[cols]
                
                print("\n --- DATOS NETLIFE ---")
                print(df.to_string(index=False))
                
                df.to_csv("data/datos_netlife.csv", index=False)
                print("\n Guardado: 'datos_netlife.csv'")
            else:
                print(" JSON vacío.")
                
        except Exception as e:
            print(f" Error IA: {e}")
            print("Raw:", respuesta.text)
    else:
        print(" No se tomaron fotos.")
            
if __name__ == "__main__":
    agente_netlife_tab_clicker()