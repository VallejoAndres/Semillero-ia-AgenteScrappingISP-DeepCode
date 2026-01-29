# run_pipeline.py
import os
import time

def ejecutar_comando(comando):
    print(f"\n🚀 Ejecutando: {comando} ...")
    codigo = os.system(comando)
    if codigo == 0:
        print("✅ Éxito.")
    else:
        print("❌ Error.")

# 1. Ejecutar Scrapers
scrapers = [
    "scrapers/claro.py",
    "scrapers/cnt.py",
    "scrapers/netlife.py",
    "scrapers/xtrim.py",
    "scrapers/gonet.py",
    "scrapers/puntonet.py",
    "scrapers/celerity.py"
]

print("--- 🕷️ INICIANDO FASE DE SCRAPING ---")
for script in scrapers:
    ejecutar_comando(f"python {script}")

# 2. Unificar
print("\n--- 🔄 INICIANDO FASE DE UNIFICACIÓN ---")
ejecutar_comando("python scrapers/data_merger.py")

# 3. Lanzar App
print("\n--- 📡 LANZANDO APLICACIÓN ---")
ejecutar_comando("streamlit run src/app.py")