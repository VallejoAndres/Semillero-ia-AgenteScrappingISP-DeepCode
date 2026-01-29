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

def agente_vision_xtrim():
    print(" Iniciando Agente Visual (Modo Infalible) para Xtrim...")
    
    objetivos = [
        {"nombre": "Fibra", "url": "https://www.xtrim.com.ec/internet/#fibra"},
        {"nombre": "Coaxial", "url": "https://www.xtrim.com.ec/internet/#coaxial"},
        {"nombre": "Preferencial", "url": "https://www.xtrim.com.ec/internet/#preferencial"}
    ]
    
    imagenes_capturadas = []
    
    with sync_playwright() as p:
        # MANTENEMOS EL MODO SIGILO (Headless = False)
        browser = p.chromium.launch(
            headless=False, 
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768}
        )
        page = context.new_page()
        
        for obj in objetivos:
            print(f"\n Entrando a: {obj['nombre']}...")
            try:
                page.goto(obj['url'], timeout=60000)
                
                # 1. TIEMPO EXTRA DE CARGA (Para asegurar que salgan las animaciones)
                print("    Esperando 8 segundos para carga completa...")
                time.sleep(8) 
                
                # 2. CLIC EN LA ESQUINA (Para cerrar modal)
                try:
                    page.mouse.click(50, 50)
                    time.sleep(2)
                except:
                    pass

                # --- FOTO 1: PARTE SUPERIOR ---
                img_top = f"xtrim_{obj['nombre']}_TOP.png"
                page.screenshot(path=img_top)
                print(f"    Foto 1 tomada (Arriba): {img_top}")
                imagenes_capturadas.append(img_top)
                
                # --- ACCIÓN: SCROLL HACIA ABAJO ---
                print("    Bajando para ver el resto de planes...")
                page.mouse.wheel(0, 600) # Bajamos 600 pixeles
                time.sleep(3) # Esperamos que se estabilice
                
                # --- FOTO 2: PARTE INFERIOR ---
                img_bottom = f"xtrim_{obj['nombre']}_BOTTOM.png"
                page.screenshot(path=img_bottom)
                print(f"    Foto 2 tomada (Abajo): {img_bottom}")
                imagenes_capturadas.append(img_bottom)
                
            except Exception as e:
                print(f"    Error en {obj['nombre']}: {e}")
        
        browser.close()

    # --- FASE IA (GEMINI) ---
    if imagenes_capturadas:
        print(f"\n Analizando {len(imagenes_capturadas)} evidencias (Arriba + Abajo)...")
        
        try:
            modelo = genai.GenerativeModel('gemini-2.5-flash')
            lista_imgs = [Image.open(img) for img in imagenes_capturadas]
            
            prompt = """
            Eres un experto analista. Tienes FOTOS SUPERIORES y FOTOS INFERIORES de la web de XTRIM.
            Algunos planes pueden repetirse en las fotos.
            
            TU MISIÓN:
            1. Extrae TODOS los planes de internet únicos.
            2. Elimina duplicados visuales.
            3. Extrae exactamente estos campos: 
               - Plan (Nombre del plan)
               - Velocidad (Solo el número y unidad, ej: 200 Mbps)
               - Precio (El precio final mensual, ej: $24.00)
               - Detalles (Info extra como instalación gratis, streaming, etc)
            
            Responde SOLO con un JSON válido (sin markdown):
            [
                {"Plan": "...", "Velocidad": "...", "Precio": "...", "Detalles": "..."}
            ]
            """
            
            respuesta = modelo.generate_content([prompt] + lista_imgs)
            texto_limpio = respuesta.text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(texto_limpio)
            
            if data:
                df = pd.DataFrame(data)
                df["Proveedor"] = "Xtrim"
                
                # Ordenar columnas
                cols = ["Proveedor", "Plan", "Velocidad", "Precio", "Detalles"]
                for col in cols:
                    if col not in df.columns: df[col] = ""
                df = df[cols]
                
                print("\n --- DATOS XTRIM ---")
                print(df.to_string(index=False))
                
                df.to_csv("data/datos_xtrim.csv", index=False)
                print("\n Guardado: 'datos_xtrim.csv'")
            else:
                print(" JSON vacío.")
                
        except Exception as e:
            print(f" Error IA: {e}")
            print("Raw response:", respuesta.text)
    else:
        print(" No hay capturas.")

if __name__ == "__main__":
    agente_vision_xtrim()