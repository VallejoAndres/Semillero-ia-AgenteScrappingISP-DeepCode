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

def agente_hibrido(url, nombre_isp):
    print(f"Iniciando Agente Hibrido (Hack + Click) en: {nombre_isp}...")
    
    imagenes_para_ia = []
    
    with sync_playwright() as p:
        # Usamos un viewport grande 
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print(f"Navegando a {url}...")
        page.goto(url, timeout=60000)
        time.sleep(5) 

# --- BUCLE DE CAPTURA (3 Vueltas) ---
        # Esto nos asegura capturar el carrusel entero (inicio, medio, final)
        
        selector_flecha = ".slick-next"
        
        for i in range(5):
            nombre_foto = f"celerity_{i}.png"
            
            # 1. Tomamos la foto actual
            print(f"Capturando Slide {i+1} ({nombre_foto})...")
            page.screenshot(path=nombre_foto)
            imagenes_para_ia.append(nombre_foto)
            
            # 2. Intentamos mover al siguiente slide
            try:
                if page.locator(selector_flecha).first.is_visible():
                    print("Haciendo clic en Siguiente >>")
                    page.locator(selector_flecha).first.click()
                    time.sleep(2) # Esperamos que se mueva la animacion
                else:
                    print("No hay mas botones de siguiente. Terminando.")
                    break
            except Exception as e:
                print(f"No se pudo avanzar mas: {e}")
                break
        
        browser.close()

    # --- FASE DE PROCESAMIENTO ARTIFICIAL ---
    print(f"Enviando {len(imagenes_para_ia)} fotos a Gemini para consolidar datos...")
    
    try:
        modelo = genai.GenerativeModel('gemini-2.5-flash')
        
        lista_imagenes = [Image.open(img) for img in imagenes_para_ia]
        
        prompt = """
        Eres un experto analista de datos. Tienes una SECUENCIA de fotos de un carrusel de planes.
        Las fotos se mueven de izquierda a derecha.
        
        TU MISION CRITICA:
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
        respuesta = modelo.generate_content([prompt] + lista_imagenes)
        texto_respuesta = respuesta.text
            
        # --- LIMPIEZA Y GUARDADO CSV ---
        # Quitamos los bloques de código si la IA los pone
        texto_limpio = texto_respuesta.replace("```json", "").replace("```", "").strip()
            
        data = json.loads(texto_limpio)
            
        if data:
            df = pd.DataFrame(data)
                # Agregamos columna de proveedor para la mezcla final
            df["Proveedor"] = "Celerity"
                
                # Reordenamos columnas
            cols = ["Proveedor", "Plan", "Velocidad", "Precio", "Detalles"]
                # Aseguramos que existan todas las columnas aunque vengan vacías
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
                        
            df = df[cols]
                
            print("\n --- DATOS CELERITY ---")
            print(df.to_string(index=False))
                
            df.to_csv("data/datos_celerity.csv", index=False)
            print("\n Archivo guardado: 'datos_celerity.csv'")
        else:
            print(" La IA devolvió una lista vacía.")
                
    except Exception as e:
        print(f" Error procesando IA o JSON: {e}")
        print("Respuesta cruda de la IA para debug:", texto_respuesta)

if __name__ == "__main__":
    url_celerity = "https://www.celerity.ec/" 
    agente_hibrido(url_celerity, "Celerity")