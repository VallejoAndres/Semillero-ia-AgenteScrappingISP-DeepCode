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
        # --- FASE 0: EL ASESINO DE COOKIES ---
        print("Detectando y eliminando banner de cookies...")
        page.evaluate("""
            () => {
                // Buscamos el modal por el ID que nos dio el error
                const modal = document.querySelector('#themaCookieModal');
                if (modal) {
                    modal.remove(); // Lo borramos del mapa
                }
                
                // Tambien borramos el fondo oscuro si existe (backdrop)
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) backdrop.remove();
                
                // A veces el body se queda bloqueado, lo liberamos
                document.body.style.overflow = 'auto';
            }
        """)
        time.sleep(2) # Esperamos a que desaparezca visualmente
        print("Banner eliminado. La vista esta despejada.")

# --- BUCLE DE CAPTURA (3 Vueltas) ---
        # Esto nos asegura capturar el carrusel entero (inicio, medio, final)
        
        selector_flecha = ".slick-next"
        
        for i in range(3):
            nombre_foto = f"claro_{i}.png"
            
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

    # --- FASE DE VISION ARTIFICIAL ---
    print(f"Enviando {len(imagenes_para_ia)} fotos a Gemini para consolidar datos...")
    
    try:
        modelo = genai.GenerativeModel('gemini-2.5-flash')
        
        lista_imagenes = [Image.open(img) for img in imagenes_para_ia]
        
        prompt = """
        Eres un experto analista de datos. Tienes una secuencia de fotos de Claro Ecuador.
        Ya NO deberia haber banners de cookies tapando los precios.
        
        TU MISION:
        1. Extrae TODOS los planes de internet.
        2. IMPORTANTE: Los precios suelen estar abajo o en letra grande. Buscalos bien.
        3. Si ves beneficios (ej: Paramount+, 300 min), agregalos en un campo 'detalles'.
        4. Elimina duplicados.
        
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
            df["Proveedor"] = "Claro"
                
                # Reordenamos columnas
            cols = ["Proveedor", "Plan", "Velocidad", "Precio", "Detalles"]
                # Aseguramos que existan todas las columnas aunque vengan vacías
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
                        
            df = df[cols]
                
            print("\n --- DATOS CLARO ---")
            print(df.to_string(index=False))
                
            df.to_csv("data/datos_claro.csv", index=False)
            print("\n Archivo guardado: 'datos_claro.csv'")
        else:
            print(" La IA devolvió una lista vacía.")
                
    except Exception as e:
        print(f"Error procesando IA o JSON: {e}")
        print("Respuesta cruda de la IA para debug:", texto_respuesta)

if __name__ == "__main__":
    url_celerity = "https://www.claro.com.ec/personas/servicios/servicios-hogar/internet/" 
    agente_hibrido(url_celerity, "Claro")