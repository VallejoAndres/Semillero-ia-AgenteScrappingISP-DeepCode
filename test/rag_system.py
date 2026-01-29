import pandas as pd
import chromadb
import google.generativeai as genai
import os
import sys

# --- 1. CONFIGURACIÓN DE RUTAS INTELIGENTE ---
# Obtenemos la ruta de donde está ESTE archivo (carpeta test)
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Obtenemos la ruta de la carpeta RAÍZ (un nivel arriba de test)
ROOT_DIR = os.path.dirname(BASE_DIR)

# Añadimos la raíz al sistema para poder importar config.py
sys.path.append(ROOT_DIR)

# --- 2. CARGAR API KEY ---
try:
    from config import API_KEY
    genai.configure(api_key=API_KEY)
except ImportError:
    print("❌ ERROR CRÍTICO: No se encontró el archivo 'config.py' en la raíz del proyecto.")
    print(f"Buscando en: {ROOT_DIR}")
    sys.exit(1)

# Forzamos UTF-8 para evitar errores de emojis en Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def construir_cerebro_rag():
    print("[INIT] Construyendo Base Vectorial (ChromaDB)...")
    
    archivo_master = "planes_internet_ecuador_master.csv"
    
    if not os.path.exists(archivo_master):
        print("[ERROR] No existe el archivo maestro. Ejecuta primero 'data_merger.py'")
        return None

    try:
        df = pd.read_csv(archivo_master, encoding='utf-8')
    except:
        df = pd.read_csv(archivo_master, encoding='latin-1')
    
    # --- 1. PREPARACIÓN DE DOCUMENTOS ---
    documents = []
    metadatas = []
    ids = []

    print(f"   [DATA] Procesando {len(df)} planes...")

    for idx, row in df.iterrows():
        plan = str(row['Plan']) if not pd.isna(row['Plan']) else "Plan Generico"
        velocidad = str(row['Velocidad']) if not pd.isna(row['Velocidad']) else "No especificada"
        precio = str(row['Precio']) if not pd.isna(row['Precio']) else "0"
        categoria = str(row['Categoría']) if not pd.isna(row['Categoría']) else "General"
        detalles = str(row['Detalles']) if not pd.isna(row['Detalles']) else ""
        proveedor = str(row['Proveedor'])

        contexto_extra = ""
        if "Gamer" in plan or "Pro" in plan:
            contexto_extra += " Ideal para videojuegos, gaming competitivo, baja latencia, streaming."
        if "Pyme" in categoria or "Negocio" in categoria:
            contexto_extra += " Recomendado para empresas, oficinas, ruc, corporativo."
        
        texto_vector = (
            f"Plan de internet del proveedor {proveedor}. "
            f"Nombre del plan: {plan}. "
            f"Velocidad: {velocidad}. "
            f"Precio mensual: {precio}. "
            f"Categoría: {categoria}. "
            f"Detalles adicionales: {detalles}. "
            f"{contexto_extra}"
        )
        
        documents.append(texto_vector)
        
        metadatas.append({
            "proveedor": proveedor,
            "plan": plan,
            "precio": precio,
            "velocidad": velocidad
        })
        
        ids.append(f"id_{idx}")

    # --- 2. INGESTIÓN EN CHROMA ---
    client = chromadb.Client() 
    
    try:
        client.delete_collection("isp_plans")
    except:
        pass
        
    collection = client.create_collection(name="isp_plans")
    
    print(f"   [PROCESANDO] Vectorizando {len(documents)} planes...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print("   [OK] Base de datos lista.")
    return collection

def consultar_al_experto(collection, pregunta):
    print(f"\n[USUARIO] Pregunta: {pregunta}")
    
    # A. BÚSQUEDA SEMÁNTICA
    results = collection.query(
        query_texts=[pregunta],
        n_results=6 
    )
    
    # B. CONSTRUCCIÓN DE CONTEXTO
    contexto_str = ""
    print("   [RAG] Planes recuperados por ChromaDB:")
    
    if not results['metadatas'][0]:
        print("      No se encontraron coincidencias cercanas.")
        return

    for i, meta in enumerate(results['metadatas'][0]):
        linea = f"- {meta['proveedor']} | Plan: {meta['plan']} | Vel: {meta['velocidad']} | Precio: {meta['precio']}"
        print(f"      {linea}")
        contexto_str += linea + "\n"
        
    # C. GENERACIÓN DE RESPUESTA (LLM)
    prompt = f"""
    Eres un asesor experto en venta de internet en Ecuador.
    Usa SOLO la siguiente información recuperada de la base de datos para responder.
    
    INFORMACIÓN DISPONIBLE:
    {contexto_str}
    
    PREGUNTA DEL CLIENTE: "{pregunta}"
    
    INSTRUCCIONES:
    1. Recomienda la(s) mejor(es) opción(es) de la lista.
    2. Compara precios y velocidades si es necesario.
    3. Si no hay nada exacto, ofrece lo más cercano.
    4. Sé amable y directo.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        print("\n[RESPUESTA IA]:")
        print("-" * 70)
        print(response.text)
        print("-" * 70)
    except Exception as e:
        print(f"\n[ERROR] Generando respuesta con Gemini: {e}")

if __name__ == "__main__":
    # 1. Crear DB
    db = construir_cerebro_rag()
    
    if db:
        # 2. Pruebas de Fuego
        consultar_al_experto(db, "Busco el plan más barato para mi casa, no quiero gastar mucho")
        
        consultar_al_experto(db, "Necesito un plan súper rápido para jugar online, soy gamer")
        
        consultar_al_experto(db, "Qué opciones tiene Netlife para un negocio?")

        consultar_al_experto(db, "Dime los mejores planes por menos de 40 dolares, comparalos con Netlife")