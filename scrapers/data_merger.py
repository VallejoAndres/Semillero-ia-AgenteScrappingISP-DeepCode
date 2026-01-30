import pandas as pd
import os
import re

def limpiar_precio(precio_str):
    """Convierte '$24,90' o 'USD 25' a un número flotante 24.90 para ordenar"""
    if pd.isna(precio_str): return 1000.0 # Ponemos precio alto si es N/A para que vaya al final
    # Quitamos todo lo que no sea digito o punto/coma
    limpio = re.sub(r'[^\d.,]', '', str(precio_str))
    limpio = limpio.replace(',', '.')
    try:
        return float(limpio)
    except:
        return 0.0
    
def normalizar_velocidad(texto):
    """
    Convierte todo a Mbps numérico.
    Ej: "1 Gbps" -> 1000
    Ej: "2000 MBPS" -> 2000
    Ej: "50 megas" -> 50
    """
    if pd.isna(texto): return 0
    texto_lower = str(texto).lower()
    
    # 1. Buscar el número (acepta decimales como 1.2 Gbps)
    match = re.search(r'(\d+(?:\.\d+)?)', texto_lower)
    if not match:
        return 0
    
    numero = float(match.group(1))
    
    # 2. Si dice 'gb' (gbps, giga), multiplicamos por 1000
    if 'gb' in texto_lower:
        numero = numero * 1000
        
    return int(numero) # Retornamos entero (ej: 1000)

def unificar_csvs():
    print("🔄 Iniciando Fusión de Datos de ISPs...")
    
    # Definimos la carpeta de datos explícitamente
    data_folder = "data" 
    
    # Lista de archivos que esperamos encontrar
    archivos = [
        "data/datos_cnt_completo.csv", 
        "data/datos_claro.csv",
        "data/datos_gonet.csv", 
        "data/datos_netlife.csv", 
        "data/datos_xtrim.csv", 
        "data/datos_puntonet.csv", 
        "data/datos_celerity.csv"
    ]
    
    dfs = []
    
    for archivo in archivos:
        if os.path.exists(archivo):
            try:
                print(f"    📂 Leyendo {archivo}...")
                df = pd.read_csv(archivo)
                
                # Normalización de Columnas
                df.rename(columns={
                    "Categoria": "Categoría",
                    "Tipo": "Categoría",
                    "Precio Final": "Precio",
                    "Precio_Final": "Precio",       
                    "Velocidad_Final": "Velocidad", 
                    "Velocidad_Bajada": "Velocidad" 
                }, inplace=True)
                
                # Asegurar columnas estándar
                if "Categoría" not in df.columns: df["Categoría"] = "Hogar"
                if "Detalles" not in df.columns: df["Detalles"] = ""
                
                # Seleccionar solo lo que nos importa
                cols_finales = ["Proveedor", "Plan", "Velocidad", "Precio", "Categoría", "Detalles"]
                
                # Rellenar columnas faltantes
                for col in cols_finales:
                    if col not in df.columns: df[col] = "N/A"
                
                # --- CORRECCIÓN IMPORTANTE: APLICAR NORMALIZACIÓN ---
                # Creamos la columna numérica AHORA
                df["Velocidad_Num"] = df["Velocidad"].apply(normalizar_velocidad)
                
                # Opcional: Estandarizar visualmente todo a "Mbps"
                mask = df["Velocidad_Num"] > 0
                df.loc[mask, "Velocidad"] = df.loc[mask, "Velocidad_Num"].astype(str) + " Mbps"

                # Guardamos incluyendo la columna numérica temporal
                dfs.append(df[cols_finales + ["Velocidad_Num"]])
                
            except Exception as e:
                print(f"    ⚠️ Error leyendo {archivo}: {e}")
        else:
            print(f"    ⚠️ No encontrado: {archivo} (Saltando...)")
    
    if dfs:
        master_df = pd.concat(dfs, ignore_index=True)
        
        # Limpieza de Precios
        master_df["Precio_Num"] = master_df["Precio"].apply(limpiar_precio)
        
        # ORDENAR: Ahora sí funciona porque Velocidad_Num existe
        master_df = master_df.sort_values(by=["Precio_Num", "Velocidad_Num"], ascending=[True, False])
        
        # Guardamos (quitamos la columna Velocidad_Num del CSV final para limpieza)
        output_file = os.path.join(data_folder, "planes_internet_ecuador_master.csv")
        master_df.drop(columns=["Velocidad_Num"]).to_csv(output_file, index=False)
        
        print("\n🏆 --- BASE MAESTRA CREADA ---")
        print(f"Total de planes: {len(master_df)}")
        # Muestra planes de alta velocidad para verificar
        print(master_df[master_df['Velocidad'].str.contains('1000|2000', na=False)][["Proveedor", "Velocidad", "Precio"]].head(5).to_string(index=False))
        print(f"\n💾 Guardado en: {output_file}")
    else:
        print("❌ No se encontraron archivos CSV para unir.")

if __name__ == "__main__":
    unificar_csvs()