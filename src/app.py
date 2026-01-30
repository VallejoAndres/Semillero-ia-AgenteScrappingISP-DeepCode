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

# --- ESTILOS PERSONALIZADOS (INPUT FIJO ABAJO) ---
st.markdown("""
<style>
body {
    background-color: #0b0f1a;
    color: #e6f1ff;
}
.stApp {
    background: linear-gradient(135deg, #0b0f1a, #10192b);
}

/* Centrar contenido principal */
.block-container {
    max-width: 1100px;
    margin: auto;
    padding-bottom: 180px; /* espacio para el input fijo */
}

/* Títulos */
h1 {
    color: #00e5ff;
    text-shadow: 0 0 10px #00e5ff, 0 0 20px #0088ff;
    text-align: center;
}
h2, h3 {
    color: #66ccff;
}

/* Mensajes del chat */
[data-testid="stChatMessage"] {
    background-color: #121a2b;
    border: 1px solid #1f2a44;
    border-radius: 12px;
    padding: 12px;
    box-shadow: 0 0 10px rgba(0,229,255,0.1);
    margin-bottom: 10px;
}

/* Tabs */
button[data-baseweb="tab"] {
    color: #9fb3c8;
    font-weight: bold;
}
button[aria-selected="true"][data-baseweb="tab"] {
    color: #00e5ff;
    border-bottom: 2px solid #00e5ff;
}

/* Métricas */
[data-testid="stMetric"] {
    background-color: #121a2b;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #1f2a44;
    box-shadow: 0 0 10px rgba(0,229,255,0.08);
}

/* Línea decorativa */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00e5ff, transparent);
    box-shadow: 0 0 10px #00e5ff;
}

/* ===== INPUT DEL CHAT FIJO ABAJO (tipo GPT) ===== */
section[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    max-width: 900px;
    min-width: 320px;
    z-index: 999;
}

/* Caja del input */
section[data-testid="stChatInput"] > div {
    background-color: #0f1726;
    border: 1px solid #00e5ff;
    border-radius: 16px;
    box-shadow: 0 0 18px rgba(0,229,255,0.35);
    padding: 10px;
}

/* Texto del input */
section[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: #e6f1ff !important;
    font-size: 16px !important;
}

/* Botón enviar */
section[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #00e5ff, #0088ff);
    border: none;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0,229,255,0.6);
}
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DE LA API KEY ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    try:
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from config import API_KEY
    except ImportError:
        st.error("❌ ERROR: No se encontró la API KEY. Crea .streamlit/secrets.toml o config.py")
        st.stop()

genai.configure(api_key=API_KEY)

# --- TÍTULO ---
st.markdown("""
<h1>🌐⚡ ISP Ecuador AI Network</h1>
<p style="text-align:center; color:#9fb3c8;">
Asesor inteligente basado en <b>IA y redes de datos</b> para encontrar el mejor plan de Internet en Ecuador.
</p>
""", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("""
<div style="
background-color:#121a2b;
padding:15px;
border-radius:12px;
border:1px solid #1f2a44;
box-shadow:0 0 15px rgba(0,229,255,0.08);
text-align:center;
">
🔎 Analiza en tiempo real los planes de  
<b>Xtrim, Netlife, Claro, Gonet, CNT, Celerity y Puntonet</b>  
usando búsqueda semántica e Inteligencia Artificial (RAG).
</div>
""", unsafe_allow_html=True)

# --- RAG ---
@st.cache_resource
def iniciar_cerebro_rag():
    archivo_master = "data/planes_internet_ecuador_master.csv"

    if not os.path.exists(archivo_master):
        st.error("❌ No encontré el CSV maestro. Ejecuta primero run_pipeline.py")
        return None, None

    try:
        df = pd.read_csv(archivo_master, encoding='utf-8')
    except:
        df = pd.read_csv(archivo_master, encoding='latin-1')

    documents, metadatas, ids = [], [], []

    for idx, row in df.iterrows():
        plan = str(row['Plan'])
        proveedor = str(row['Proveedor'])

        texto = f"Proveedor: {proveedor}. Plan: {plan}. Velocidad: {row['Velocidad']}. Precio: {row['Precio']}. Detalles: {row['Detalles']}."

        if "Gamer" in plan or "Pro" in plan:
            texto += " Ideal para gaming."
        if "Pyme" in str(row.get('Categoría', '')):
            texto += " Ideal para negocios."

        documents.append(texto)
        metadatas.append({
            "proveedor": proveedor,
            "precio": str(row['Precio']),
            "plan": plan,
            "velocidad": str(row['Velocidad'])
        })
        ids.append(f"id_{idx}")

    client = chromadb.Client()
    try:
        client.delete_collection("isp_plans_app")
    except:
        pass

    collection = client.create_collection(name="isp_plans_app")
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    return collection, df

collection, df_master = iniciar_cerebro_rag()
if collection is None:
    st.stop()

tab1, tab2 = st.tabs(["💬 Chat IA", "📊 Base de Planes"])

# -------- CHAT --------
with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # mostrar historial (va creciendo hacia arriba)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # input SIEMPRE FIJO ABAJO
    prompt = st.chat_input("Ej: plan para gaming menor a $50")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("🔍 Analizando red de planes..."):
                results = collection.query(query_texts=[prompt], n_results=60)

                contexto = ""
                if results['metadatas'][0]:
                    for meta in results['metadatas'][0]:
                        contexto += f"- {meta['proveedor']} | {meta['plan']} | {meta['velocidad']} | {meta['precio']}\n"

                historial_chat = ""
                for msg in st.session_state.messages[-5:]:
                    role = "Cliente" if msg["role"] == "user" else "Experto"
                    historial_chat += f"{role}: {msg['content']}\n"

                modelo = genai.GenerativeModel('gemini-2.5-flash')

                prompt_ia = f"""
Eres un asesor experto en planes de Internet en Ecuador.

HISTORIAL:
{historial_chat}

PLANES DISPONIBLES:
{contexto}

Pregunta del cliente: "{prompt}"

Responde claro, compara opciones y recomienda la mejor.
Usa listas o tablas en Markdown.
"""

                try:
                    response = modelo.generate_content(prompt_ia)
                    respuesta_texto = response.text
                except Exception as e:
                    respuesta_texto = f"⚠️ Error de IA: {e}"

                st.markdown(respuesta_texto)

        st.session_state.messages.append({"role": "assistant", "content": respuesta_texto})
        st.rerun()  # hace que el chat se redibuje y “baje” como en GPT

# -------- DATOS --------
with tab2:
    st.header("📡 Base de Datos de Planes")
    st.dataframe(df_master, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("Total de planes encontrados", len(df_master))
    col2.bar_chart(df_master['Proveedor'].value_counts())