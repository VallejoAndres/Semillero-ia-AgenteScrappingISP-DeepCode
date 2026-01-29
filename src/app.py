import streamlit as st
import pandas as pd
import google.generativeai as genai
import chromadb
import os
import sys

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="ISP Ecuador AI",
    page_icon="📡",
    layout="wide"
)

# --- CONFIGURACIÓN DE LA API KEY ---
try:
    # 1. Intentamos leer de los secretos nativos de Streamlit (Lo mejor para Nube y Local)
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except FileNotFoundError:
    # 2. Si no existe secrets.toml, intentamos leer de config.py en la carpeta raíz
    try:
        # Truco para importar config.py desde la carpeta superior
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from config import API_KEY
    except ImportError:
        st.error("❌ ERROR: No se encontró la API KEY. Crea el archivo .streamlit/secrets.toml")
        st.stop()

genai.configure(api_key=API_KEY)
# -------------------------------------------------------

# --- TÍTULO Y ESTILO ---
st.title(" Asesor de Internet Ecuador (AI Powered)")
st.markdown("""
Esta herramienta usa **Inteligencia Artificial (RAG)** para buscar en tiempo real 
entre los planes de **Xtrim, Netlife, Claro, Gonet, CNT, Celerity y Puntonet**.
""")

# --- CACHÉ DEL SISTEMA RAG ---
# Usamos @st.cache_resource para no reconstruir la base de datos en cada clic
@st.cache_resource
def iniciar_cerebro_rag():
    archivo_master = "data/planes_internet_ecuador_master.csv"
    if not os.path.exists(archivo_master):
        st.error("❌ No encontré 'planes_internet_ecuador_master.csv'. Ejecuta los scrapers primero.")
        return None

    try:
        df = pd.read_csv(archivo_master, encoding='utf-8')
    except:
        df = pd.read_csv(archivo_master, encoding='latin-1')

    # Preparar datos para Chroma
    documents = []
    metadatas = []
    ids = []

    for idx, row in df.iterrows():
        # Construcción del texto semántico
        plan = str(row['Plan'])
        proveedor = str(row['Proveedor'])
        texto = f"Proveedor: {proveedor}. Plan: {plan}. Vel: {row['Velocidad']}. Precio: {row['Precio']}. Detalles: {row['Detalles']}."
        
        # Enriquecimiento
        if "Gamer" in plan or "Pro" in plan: texto += " Ideal gaming."
        if "Pyme" in str(row['Categoría']): texto += " Ideal negocios."

        documents.append(texto)
        metadatas.append({"proveedor": proveedor, "precio": str(row['Precio']), "plan": plan, "velocidad": str(row['Velocidad'])})
        ids.append(f"id_{idx}")

    # Iniciar ChromaDB en memoria
    client = chromadb.Client()
    try: client.delete_collection("isp_plans_app")
    except: pass
    
    collection = client.create_collection(name="isp_plans_app")
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    
    return collection, df

# Iniciamos el sistema
collection, df_master = iniciar_cerebro_rag()

# --- INTERFAZ PRINCIPAL ---
tab1, tab2 = st.tabs(["💬 Chat con el Asesor", "📊 Ver Todos los Planes"])

# --- TAB 1: CHATBOT RAG ---
with tab1:
    # Inicializar historial
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar mensajes previos
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("Ej: Busco un plan de Netlife para un negocio por menos de $40"):
        # 1. Mostrar pregunta usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Lógica RAG
        with st.chat_message("assistant"):
            with st.spinner("Analizando base de datos de proveedores..."):
                # A. Búsqueda Vectorial (Traemos todos los resultados para comparar bien)
                results = collection.query(query_texts=[prompt], n_results=60)
                
                contexto = ""
                if results['metadatas'][0]:
                    for meta in results['metadatas'][0]:
                        contexto += f"- {meta['proveedor']} | {meta['plan']} | {meta['velocidad']} | {meta['precio']}\n"

                # B. Construir el HISTORIAL para la IA
                    # Tomamos los últimos 4 mensajes para no saturar, pero suficiente para contexto
                    historial_chat = ""
                    for msg in st.session_state.messages[-5:]: 
                        role = "Cliente" if msg["role"] == "user" else "Experto"
                        historial_chat += f"{role}: {msg['content']}\n"
                        
                # C. Generación con Gemini
                modelo = genai.GenerativeModel('gemini-2.5-flash')
                prompt_ia = f"""
                Eres un vendedor experto de internet en Ecuador.
                Usa esta lista de planes reales para responder al cliente.

                HISTORIAL DE CONVERSACIÓN:
                {historial_chat}
                
                PLANES ENCONTRADOS:
                {contexto}
                
                PREGUNTA: "{prompt}"
                
                - Sé amable y usa formato Markdown (negritas, listas).
                - Si comparas, usa una tabla o lista clara.
                - Recomienda lo mejor según precio/velocidad.
                """
                try:
                    response = modelo.generate_content(prompt_ia)
                    respuesta_texto = response.text
                except Exception as e:
                    respuesta_texto = f"Error de conexión con la IA: {e}"

                st.markdown(respuesta_texto)
        
        # 3. Guardar respuesta
        st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})

# --- TAB 2: EXPLORADOR DE DATOS ---
with tab2:
    st.header("Base de Datos Maestra")
    st.dataframe(df_master)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Planes Rastreados", len(df_master))
    with col2:
        conteo = df_master['Proveedor'].value_counts()
        st.bar_chart(conteo)