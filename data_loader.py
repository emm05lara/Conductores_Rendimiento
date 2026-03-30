import os
import pandas as pd

# =============================================================================
# CONFIGURACIÓN INICIAL — Ajusta aquí la ruta de tu archivo Excel
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Mantengo el nombre de la variable "RUTA_EXCEL" y "NOMBRE_HOJA" para no romper imports en app.py
RUTA_EXCEL = os.path.join(BASE_DIR, "data", "conductores.csv")
NOMBRE_HOJA = "conductores"

# Nombres exactos de las columnas en tu Excel
# Ajusta estos valores si los nombres difieren en el archivo real
COL_CONDUCTOR     = "CONDUCTOR"
COL_GANANCIAS     = "GANANCIAS TOTALES"
COL_META          = "META"
COL_COMENTARIO    = "COMENTARIO"

# Columnas de fecha — el script detectará cuáles existen automáticamente
COL_FECHA         = "FECHA"          # columna de fecha completa (si existe)
COL_AÑO           = "AÑO"           # columna de año (si existe)
COL_SEM           = "SEM"           # columna de semana (si existe)

# =============================================================================
# FUNCIONES DE CARGA Y PREPARACIÓN DE DATOS
# =============================================================================

def cargar_datos(ruta: str) -> pd.DataFrame:
    """
    Carga el archivo CSV y retorna un DataFrame con manejo de codificación.
    Lanza excepciones descriptivas si el archivo no existe.
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"No se encontró el archivo de datos en:\n  {ruta}\n"
            "Verifica que la variable de ruta sea correcta."
        )

    try:
        # Intentar primero con utf-8
        df = pd.read_csv(ruta, encoding='utf-8')
    except UnicodeDecodeError:
        # Fallback a latin1 si utf-8 falla
        df = pd.read_csv(ruta, encoding='latin1')
    except Exception as e:
        raise ValueError(
            f"Error al parsear el CSV:\n  {str(e)}\n"
            "Verifica la estructura de tu archivo."
        )

    print(f"[OK] Archivo cargado: {len(df)} filas, {len(df.columns)} columnas.")
    print(f"     Columnas encontradas: {list(df.columns)}")
    return df


def validar_columnas(df: pd.DataFrame) -> None:
    """
    Verifica que las columnas esenciales existan en el DataFrame.
    """
    columnas_requeridas = [COL_CONDUCTOR, COL_GANANCIAS, COL_META]
    faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if faltantes:
        raise KeyError(
            f"Las siguientes columnas no se encontraron en los datos cargados:\n"
            f"  {faltantes}\n"
            "Revisa los nombres de columna en tu CSV y ajusta las variables al inicio del script."
        )


def construir_eje_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta la estructura temporal del DataFrame y crea la columna 'PERIODO'
    para usar en el eje X, ordenada cronológicamente.

    Prioridad:
      1. Columna de fecha completa (COL_FECHA)
      2. Columnas AÑO + SEM  → etiqueta "YYYY - Sem NN"
      3. Sin información temporal → índice de fila como proxy
    """
    df = df.copy()

    if COL_FECHA in df.columns:
        # Intentar parsear la columna de fecha
        df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors="coerce")
        df["PERIODO"] = df[COL_FECHA]
        df["ETIQUETA_PERIODO"] = df[COL_FECHA].dt.strftime("%Y-%m-%d")
        df = df.sort_values("PERIODO")
        print("[OK] Eje temporal construido a partir de la columna FECHA.")

    elif COL_AÑO in df.columns and COL_SEM in df.columns:
        # Construir etiqueta legible a partir de AÑO y SEM
        def safe_int(x):
            try:
                # Intermediario float para limpiar cosas como '2024.0'
                return int(float(str(x).replace(",", "")))
            except (ValueError, TypeError):
                return None

        df["_AÑO_INT"] = df[COL_AÑO].apply(safe_int)
        df["_SEM_INT"]  = df[COL_SEM].apply(safe_int)

        # Crear un valor numérico para ordenar cronológicamente
        df["PERIODO_NUM"] = df["_AÑO_INT"] * 100 + df["_SEM_INT"].fillna(0)
        df["PERIODO"] = df["PERIODO_NUM"]
        
        # Formatear la etiqueta quitando los decimales (evitar "2024.0 - Sem 15.0")
        año_str = df["_AÑO_INT"].fillna(0).astype(int).astype(str).replace("0", "N/A")
        sem_str = df["_SEM_INT"].fillna(0).astype(int).astype(str).replace("0", "N/A")
        df["ETIQUETA_PERIODO"] = año_str + " - Sem " + sem_str
        
        df = df.sort_values("PERIODO_NUM")
        df.drop(columns=["_AÑO_INT", "_SEM_INT", "PERIODO_NUM"], inplace=True)
        print("[OK] Eje temporal construido a partir de AÑO + SEM.")

    elif COL_AÑO in df.columns:
        def safe_int_year(x):
            try:
                return int(float(str(x).replace(",", "")))
            except (ValueError, TypeError):
                return None
        df["_AÑO_INT"] = df[COL_AÑO].apply(safe_int_year)
        df["PERIODO"] = df["_AÑO_INT"]
        df["ETIQUETA_PERIODO"] = df["_AÑO_INT"].fillna(0).astype(int).astype(str).replace("0", "N/A")
        df = df.sort_values("PERIODO")
        df.drop(columns=["_AÑO_INT"], inplace=True)
        print("[OK] Eje temporal construido solo con AÑO.")

    else:
        # Sin información temporal: usar el índice del DataFrame como proxy
        df = df.reset_index(drop=True)
        df["PERIODO"] = df.index
        df["ETIQUETA_PERIODO"] = "Reg. " + (df.index + 1).astype(str)
        print("[AVISO] No se detectó columna de fecha/año/sem. Se usa el índice de fila como eje temporal.")

    return df


def preparar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara el DataFrame para graficar:
    - Construye el eje temporal.
    - Convierte GANANCIAS TOTALES y META a numérico (sin eliminar nulos ni ceros).
    """
    df = construir_eje_temporal(df)

    # Función para limpiar caracteres monetarios y espacios antes de convertir a numérico
    def limpiar_numeros(serie):
        if serie.dtype == 'object':
            # Quita símbolo $, comas de miles y espacios
            serie = serie.astype(str).str.replace(r'[\$,\s]', '', regex=True)
        return pd.to_numeric(serie, errors="coerce")

    # Convertir a numérico limpiando primero — errores producen NaN (no se eliminan)
    df[COL_GANANCIAS] = limpiar_numeros(df[COL_GANANCIAS])
    df[COL_META]      = limpiar_numeros(df[COL_META])

    # Asegurar que CONDUCTOR sea string limpio y tratar nulos
    df[COL_CONDUCTOR] = df[COL_CONDUCTOR].fillna("Desconocido").astype(str).str.strip()

    # Asegurar que COMENTARIO funcione bien aunque tenga vacíos
    if COL_COMENTARIO in df.columns:
        df[COL_COMENTARIO] = df[COL_COMENTARIO].fillna("").astype(str)

    return df


# =============================================================================
# CARGA Y VALIDACIÓN AL INICIAR
# =============================================================================

try:
    df_raw = cargar_datos(RUTA_EXCEL)
    validar_columnas(df_raw)
    df_global = preparar_datos(df_raw)
    lista_conductores = sorted(df_global[COL_CONDUCTOR].dropna().unique().tolist())

    # ── Lista global de años disponibles (para el dropdown de AÑO) ────────────
    if COL_AÑO in df_global.columns:
        def _a_entero(x):
            try:
                return int(float(x))
            except (ValueError, TypeError):
                return None
        lista_años_global = sorted(
            {_a_entero(v) for v in df_global[COL_AÑO].dropna()} - {None}
        )
    else:
        lista_años_global = []

    ERROR_CARGA = None
except Exception as e:
    df_global = pd.DataFrame()
    lista_conductores = []
    lista_años_global = []
    ERROR_CARGA = str(e)
    print(f"[ERROR] {e}")
