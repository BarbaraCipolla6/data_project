"""
data_loader.py — Funciones de carga, caché y guardado de datos.

Maneja la lectura de los datasets crudos (Steam y Sales) y los datasets
procesados, con optimización de tipos de datos para reducir uso de memoria.
"""

import os
import sys
import pandas as pd
import numpy as np

# Fix encoding for Windows console (emojis / unicode)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ============================================================================
# RUTAS POR DEFECTO
# ============================================================================

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

# Archivos fuente originales
STEAM_RAW_FILENAME = 'games_march2025_cleaned.csv'
SALES_RAW_FILENAME = 'Video Games Sales (1980-2024) - Raw.csv'


# ============================================================================
# FUNCIONES DE CARGA
# ============================================================================

def load_steam_raw(filepath: str = None) -> pd.DataFrame:
    """Carga el dataset crudo de Steam con tipos optimizados.

    Args:
        filepath: Ruta al archivo CSV. Si es None, busca en data/raw/.

    Returns:
        DataFrame con los datos crudos de Steam.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta especificada.
    """
    if filepath is None:
        filepath = os.path.join(RAW_DIR, STEAM_RAW_FILENAME)

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"No se encontró el archivo Steam en: {filepath}\n"
            f"Asegurate de copiar '{STEAM_RAW_FILENAME}' a la carpeta data/raw/"
        )

    # Columnas pesadas que no necesitamos cargar para análisis
    cols_to_skip = ['detailed_description', 'about_the_game', 'reviews',
                    'header_image', 'website', 'support_url', 'support_email',
                    'metacritic_url', 'packages']

    # Leer todas las columnas primero para obtener la lista
    all_cols = pd.read_csv(filepath, nrows=0).columns.tolist()
    use_cols = [c for c in all_cols if c not in cols_to_skip]

    print(f"📂 Cargando Steam dataset desde: {filepath}")
    print(f"   Columnas seleccionadas: {len(use_cols)} de {len(all_cols)}")

    df = pd.read_csv(filepath, usecols=use_cols, low_memory=False)

    print(f"   ✅ Cargadas {len(df):,} filas × {len(df.columns)} columnas")
    print(f"   💾 Memoria: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

    return df


def load_sales_raw(filepath: str = None) -> pd.DataFrame:
    """Carga el dataset crudo de Video Games Sales.

    Args:
        filepath: Ruta al archivo CSV. Si es None, busca en data/raw/.

    Returns:
        DataFrame con los datos crudos de ventas.

    Raises:
        FileNotFoundError: Si el archivo no existe en la ruta especificada.
    """
    if filepath is None:
        filepath = os.path.join(RAW_DIR, SALES_RAW_FILENAME)

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"No se encontró el archivo de ventas en: {filepath}\n"
            f"Asegurate de copiar '{SALES_RAW_FILENAME}' a la carpeta data/raw/"
        )

    # Columnas a descartar
    cols_to_skip = ['img', 'last_update']

    all_cols = pd.read_csv(filepath, nrows=0).columns.tolist()
    use_cols = [c for c in all_cols if c not in cols_to_skip]

    print(f"📂 Cargando Sales dataset desde: {filepath}")

    df = pd.read_csv(filepath, usecols=use_cols, low_memory=False)

    print(f"   ✅ Cargadas {len(df):,} filas × {len(df.columns)} columnas")
    print(f"   💾 Memoria: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

    return df


def load_clean_data(filename: str) -> pd.DataFrame:
    """Carga un dataset procesado desde la carpeta data/processed/.

    Args:
        filename: Nombre del archivo (ej: 'steam_clean.csv').

    Returns:
        DataFrame con los datos procesados.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    filepath = os.path.join(PROCESSED_DIR, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"No se encontró el archivo procesado: {filepath}\n"
            f"Ejecutá primero el script 01_limpieza_transformacion.py"
        )

    print(f"📂 Cargando dataset procesado: {filename}")
    df = pd.read_csv(filepath, low_memory=False)
    print(f"   ✅ Cargadas {len(df):,} filas × {len(df.columns)} columnas")

    return df


# ============================================================================
# FUNCIONES DE GUARDADO
# ============================================================================

def save_processed(df: pd.DataFrame, filename: str, index: bool = False) -> str:
    """Guarda un DataFrame procesado en la carpeta data/processed/.

    Args:
        df: DataFrame a guardar.
        filename: Nombre del archivo (ej: 'steam_clean.csv').
        index: Si incluir el índice en el CSV.

    Returns:
        Ruta completa del archivo guardado.
    """
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    filepath = os.path.join(PROCESSED_DIR, filename)

    df.to_csv(filepath, index=index)

    size_mb = os.path.getsize(filepath) / 1e6
    print(f"💾 Guardado: {filename}")
    print(f"   {len(df):,} filas × {len(df.columns)} columnas | {size_mb:.1f} MB")

    return filepath


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_project_root() -> str:
    """Retorna la ruta raíz del proyecto."""
    return BASE_DIR


def get_figures_dir() -> str:
    """Retorna la ruta a la carpeta de figuras, creándola si no existe."""
    figures_dir = os.path.join(BASE_DIR, 'output', 'figures')
    os.makedirs(figures_dir, exist_ok=True)
    return figures_dir


def print_dataframe_info(df: pd.DataFrame, name: str = "DataFrame") -> None:
    """Imprime un resumen informativo de un DataFrame.

    Args:
        df: DataFrame a describir.
        name: Nombre descriptivo para el output.
    """
    print(f"\n{'='*60}")
    print(f"📊 {name}")
    print(f"{'='*60}")
    print(f"Dimensiones: {df.shape[0]:,} filas × {df.shape[1]} columnas")
    print(f"Memoria: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

    null_cols = df.isnull().sum()
    null_cols = null_cols[null_cols > 0]
    if len(null_cols) > 0:
        print(f"\nColumnas con nulos ({len(null_cols)}):")
        for col, count in null_cols.sort_values(ascending=False).head(10).items():
            pct = count / len(df) * 100
            print(f"  • {col}: {count:,} ({pct:.1f}%)")
    else:
        print("\n✅ Sin valores nulos")

    print(f"\nTipos de datos:")
    for dtype, count in df.dtypes.value_counts().items():
        print(f"  • {dtype}: {count} columnas")
