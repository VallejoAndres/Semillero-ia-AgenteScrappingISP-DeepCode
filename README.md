# 📡 Asesor de Internet Ecuador con IA (RAG)

Este proyecto es un sistema inteligente que recopila, unifica y analiza los planes de internet de los principales proveedores de Ecuador (Xtrim, Netlife, Claro, CNT, Celerity, Puntonet).

Utiliza **Web Scraping**, **Ingeniería de Datos** y **RAG (Retrieval-Augmented Generation)** para permitir a los usuarios chatear con una IA y encontrar el mejor plan.

Integrantes:
* Andres Vallejo(@VallejoAndres)
* Victor Perez (@PerezVictor20)

## 🛠️ Tecnologías Usadas
* **Python 3.11**
* **Streamlit:** Para la interfaz web interactiva.
* **Google Gemini (LLM):** Para el razonamiento y generación de respuestas.
* **ChromaDB:** Base de datos vectorial para la búsqueda semántica.
* **Playwright & Pandas:** Para la extracción y manipulación de datos.

## 📂 Estructura del Proyecto
* `app.py`: Aplicación principal (Chatbot).
* `scrapers/`: Scripts autónomos para extraer datos de cada web.
* `data/`: Archivos CSV procesados y base de datos maestra.

## 🚀 Cómo ejecutarlo localmente

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   playwright install

2. Crear una carpeta llamada .streamlit/ en la raiz del proyecto y añadir un archivo llamado secrets.toml con tu API KEY de Google:
   ```toml
   [secrets]
   GOOGLE_API_KEY = "TU_API_KEY"
   ```

3. Edita el archivo llamado `config.py` y agrega tu clave de API de Google.

4. Ejecutar el script `run_pipeline.py` para que inicie el asistente.


## 🎞️ Enlace del video
https://www.youtube.com/watch?v=VhtFDVoyPwY