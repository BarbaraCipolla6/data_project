"""
01_limpieza_transformacion.py — Fase 1: ETL (Extract, Transform, Load)

Este script realiza la limpieza y transformación de los dos datasets:
1. Steam Games (games_march2025_cleaned.csv) — 89,618 juegos
2. Video Games Sales (Video Games Sales (1980-2024) - Raw.csv) — 64,016 registros

Genera datasets procesados en data/processed/ listos para análisis.

Uso:
    python notebooks/01_limpieza_transformacion.py
"""

import os
import sys
import numpy as np
import pandas as pd

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Agregar el directorio raíz del proyecto al path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.data_loader import (
    load_steam_raw, load_sales_raw, save_processed,
    print_dataframe_info, get_figures_dir
)
from utils.cleaning import (
    parse_string_list, parse_tag_dict, parse_owner_range,
    categorize_price, parse_sales_date, standardize_console_name,
    categorize_console_generation, get_console_manufacturer
)
from utils.transformations import (
    add_temporal_features, add_review_features, add_product_features,
    add_owner_features, add_sales_features, explode_genres,
    extract_top_tags
)


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Rutas a los archivos fuente originales (en Downloads)
STEAM_SOURCE = r'C:\Users\barba\Downloads\games_march2025_cleaned.csv'
SALES_SOURCE = r'C:\Users\barba\Downloads\Video Games Sales (1980-2024) - Raw.csv'


def print_section(title: str) -> None:
    """Imprime un separador de sección."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


# ============================================================================
# FASE 1A: LIMPIEZA DEL DATASET DE STEAM
# ============================================================================

def clean_steam_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y transforma el dataset de Steam.

    Operaciones:
        1. Parsear columnas con strings de listas/dicts
        2. Parsear estimated_owners
        3. Agregar features temporales
        4. Agregar features de reviews
        5. Agregar features de producto
        6. Agregar features de owners/popularidad
        7. Eliminar columnas innecesarias
        8. Reportar calidad de datos

    Args:
        df: DataFrame crudo de Steam.

    Returns:
        DataFrame limpio y transformado.
    """
    print_section("1A. LIMPIEZA DEL DATASET DE STEAM")
    original_rows = len(df)

    # ----------------------------------------------------------------
    # 1. Parsear columnas con strings de listas Python
    # ----------------------------------------------------------------
    print("📋 Parseando columnas de listas...")
    list_columns = ['genres', 'developers', 'publishers', 'categories',
                    'supported_languages', 'full_audio_languages']
    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].apply(parse_string_list)
            non_empty = df[col].apply(len).gt(0).sum()
            print(f"   • {col}: {non_empty:,} con datos ({non_empty/len(df)*100:.1f}%)")

    # Parsear screenshots y movies como listas (para contar)
    for col in ['screenshots', 'movies']:
        if col in df.columns:
            df[col] = df[col].apply(parse_string_list)

    # ----------------------------------------------------------------
    # 2. Parsear tags (string de dict Python)
    # ----------------------------------------------------------------
    print("\n🏷️  Parseando tags...")
    df['tags'] = df['tags'].apply(parse_tag_dict)
    has_tags = df['tags'].apply(len).gt(0).sum()
    print(f"   • {has_tags:,} juegos con tags ({has_tags/len(df)*100:.1f}%)")

    # Extraer top 5 tags por juego
    df['top_tags'] = df['tags'].apply(lambda x: extract_top_tags(x, n=5))

    # ----------------------------------------------------------------
    # 3. Parsear estimated_owners
    # ----------------------------------------------------------------
    print("\n👥 Parseando estimated_owners...")
    owner_data = df['estimated_owners'].apply(parse_owner_range)
    df['owners_min'] = owner_data.apply(lambda x: x[0])
    df['owners_max'] = owner_data.apply(lambda x: x[1])
    df['owners_midpoint'] = owner_data.apply(lambda x: x[2])
    print(f"   • Rango: {df['owners_midpoint'].min():,} – {df['owners_midpoint'].max():,}")
    print(f"   • Mediana: {df['owners_midpoint'].median():,.0f}")

    # ----------------------------------------------------------------
    # 4. Features temporales
    # ----------------------------------------------------------------
    print("\n📅 Agregando features temporales...")
    df = add_temporal_features(df, 'release_date')
    print(f"   • Años: {df['year'].min()} – {df['year'].max()}")
    print(f"   • Décadas: {sorted(df['decade'].dropna().unique().tolist())}")

    # ----------------------------------------------------------------
    # 5. Features de reviews
    # ----------------------------------------------------------------
    print("\n⭐ Agregando features de reviews...")
    df = add_review_features(df)
    has_reviews = df['review_ratio'].notna().sum()
    print(f"   • Juegos con reviews: {has_reviews:,}")
    print(f"   • Review ratio medio: {df['review_ratio'].mean():.3f}")

    # ----------------------------------------------------------------
    # 6. Features de producto
    # ----------------------------------------------------------------
    print("\n🎮 Agregando features de producto...")
    df = add_product_features(df)
    print(f"   • Géneros únicos: {df['primary_genre'].nunique()}")
    print(f"   • Idiomas promedio: {df['num_languages'].mean():.1f}")
    print(f"   • Juegos gratuitos: {df['is_free'].sum():,}")

    # ----------------------------------------------------------------
    # 7. Features de popularidad
    # ----------------------------------------------------------------
    print("\n🏆 Agregando features de popularidad...")
    df = add_owner_features(df)
    print("   Distribución de popularity_tier:")
    tier_counts = df['popularity_tier'].value_counts().sort_index()
    for tier, count in tier_counts.items():
        pct = count / len(df) * 100
        print(f"   • {tier}: {count:,} ({pct:.1f}%)")

    # ----------------------------------------------------------------
    # 8. Eliminar columnas innecesarias
    # ----------------------------------------------------------------
    print("\n🗑️  Eliminando columnas innecesarias...")
    cols_to_drop = ['score_rank', 'notes', 'screenshots', 'movies',
                    'short_description', 'release_date']
    cols_existing = [c for c in cols_to_drop if c in df.columns]
    df = df.drop(columns=cols_existing)
    print(f"   • Eliminadas: {cols_existing}")

    # ----------------------------------------------------------------
    # 9. Reporte de calidad
    # ----------------------------------------------------------------
    print(f"\n✅ Steam dataset limpio:")
    print(f"   • Filas: {len(df):,} (de {original_rows:,} originales)")
    print(f"   • Columnas: {len(df.columns)}")
    print(f"   • Filas eliminadas: {original_rows - len(df):,}")

    return df


# ============================================================================
# FASE 1B: LIMPIEZA DEL DATASET DE VENTAS
# ============================================================================

def clean_sales_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y transforma el dataset de Video Games Sales.

    Operaciones:
        1. Parsear fechas
        2. Estandarizar nombres de consolas
        3. Agregar generación y fabricante
        4. Limpiar publishers/developers
        5. Agregar features de ventas regionales
        6. Eliminar columnas innecesarias

    Args:
        df: DataFrame crudo de ventas.

    Returns:
        DataFrame limpio y transformado.
    """
    print_section("1B. LIMPIEZA DEL DATASET DE VENTAS")
    original_rows = len(df)

    # ----------------------------------------------------------------
    # 1. Parsear fechas
    # ----------------------------------------------------------------
    print("📅 Parseando fechas...")
    df['release_date_dt'] = df['release_date'].apply(parse_sales_date)
    df['year'] = df['release_date_dt'].dt.year.astype('Int64')
    valid_dates = df['release_date_dt'].notna().sum()
    print(f"   • Fechas válidas: {valid_dates:,} ({valid_dates/len(df)*100:.1f}%)")
    print(f"   • Rango: {df['year'].min()} – {df['year'].max()}")

    # ----------------------------------------------------------------
    # 2. Estandarizar consolas
    # ----------------------------------------------------------------
    print("\n🎮 Estandarizando consolas...")
    df['console_full'] = df['console'].apply(standardize_console_name)
    df['console_generation'] = df['console'].apply(categorize_console_generation)
    df['console_manufacturer'] = df['console'].apply(get_console_manufacturer)

    print(f"   • Consolas únicas: {df['console'].nunique()}")
    print(f"   • Generaciones: {sorted(df['console_generation'].unique().tolist())}")
    print("   • Fabricantes:")
    for mfg, count in df['console_manufacturer'].value_counts().head(6).items():
        print(f"     - {mfg}: {count:,}")

    # ----------------------------------------------------------------
    # 3. Limpiar publishers/developers
    # ----------------------------------------------------------------
    print("\n🏢 Limpiando publishers/developers...")
    df['publisher_known'] = df['publisher'] != 'Unknown'
    df['developer_known'] = df['developer'] != 'Unknown'
    unknown_pub = (~df['publisher_known']).sum()
    unknown_dev = (~df['developer_known']).sum()
    print(f"   • Publishers desconocidos: {unknown_pub:,} ({unknown_pub/len(df)*100:.1f}%)")
    print(f"   • Developers desconocidos: {unknown_dev:,} ({unknown_dev/len(df)*100:.1f}%)")

    # ----------------------------------------------------------------
    # 4. Features de ventas regionales
    # ----------------------------------------------------------------
    print("\n💰 Agregando features de ventas regionales...")
    df = add_sales_features(df)

    has_sales = df['total_sales'].notna().sum()
    print(f"   • Juegos con datos de ventas: {has_sales:,} ({has_sales/len(df)*100:.1f}%)")

    if has_sales > 0:
        print("   • Región dominante (distribución):")
        for region, count in df[df['total_sales'].notna()]['dominant_region'].value_counts().items():
            pct = count / has_sales * 100
            print(f"     - {region}: {count:,} ({pct:.1f}%)")

    # ----------------------------------------------------------------
    # 5. Década
    # ----------------------------------------------------------------
    df['decade'] = (df['year'] // 10 * 10).astype('Int64')

    # ----------------------------------------------------------------
    # 6. Reporte de calidad
    # ----------------------------------------------------------------
    print(f"\n✅ Sales dataset limpio:")
    print(f"   • Filas: {len(df):,} (de {original_rows:,} originales)")
    print(f"   • Columnas: {len(df.columns)}")

    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Ejecuta el pipeline completo de limpieza y transformación."""
    print_section("PIPELINE DE LIMPIEZA Y TRANSFORMACIÓN")
    print("Proyecto: Análisis del Mercado de Videojuegos")
    print("Datasets: Steam (2025) + Video Games Sales (1980–2024)")

    # ====================================================================
    # CARGAR DATOS CRUDOS
    # ====================================================================
    print_section("CARGA DE DATOS")

    # Intentar cargar desde data/raw/ primero, si no desde Downloads
    try:
        steam_raw = load_steam_raw()
    except FileNotFoundError:
        print("   ⚠️  No encontrado en data/raw/, cargando desde Downloads...")
        steam_raw = load_steam_raw(STEAM_SOURCE)

    try:
        sales_raw = load_sales_raw()
    except FileNotFoundError:
        print("   ⚠️  No encontrado en data/raw/, cargando desde Downloads...")
        sales_raw = load_sales_raw(SALES_SOURCE)

    print_dataframe_info(steam_raw, "Steam Raw Dataset")
    print_dataframe_info(sales_raw, "Sales Raw Dataset")

    # ====================================================================
    # LIMPIAR DATASETS
    # ====================================================================
    steam_clean = clean_steam_dataset(steam_raw)
    sales_clean = clean_sales_dataset(sales_raw)

    # ====================================================================
    # GUARDAR DATASETS PROCESADOS
    # ====================================================================
    print_section("GUARDADO DE DATASETS PROCESADOS")

    # Steam limpio — seleccionar columnas para el CSV (sin listas/dicts)
    # Las columnas con listas se guardan como strings para CSV
    steam_for_csv = steam_clean.copy()

    # Convertir listas a strings para guardar en CSV
    list_cols = ['genres', 'developers', 'publishers', 'categories',
                 'supported_languages', 'full_audio_languages', 'top_tags']
    for col in list_cols:
        if col in steam_for_csv.columns:
            steam_for_csv[col] = steam_for_csv[col].apply(str)

    # Convertir dict tags a string
    if 'tags' in steam_for_csv.columns:
        steam_for_csv['tags'] = steam_for_csv['tags'].apply(str)

    save_processed(steam_for_csv, 'steam_clean.csv')
    save_processed(sales_clean, 'sales_clean.csv')

    # Géneros explotados (una fila por género por juego)
    genres_exploded = explode_genres(steam_clean)
    save_processed(genres_exploded, 'genres_exploded.csv')

    # ====================================================================
    # RESUMEN FINAL
    # ====================================================================
    print_section("RESUMEN FINAL")

    print("📊 Datasets generados en data/processed/:")
    print(f"   1. steam_clean.csv      → {len(steam_for_csv):,} filas × {len(steam_for_csv.columns)} cols")
    print(f"   2. sales_clean.csv      → {len(sales_clean):,} filas × {len(sales_clean.columns)} cols")
    print(f"   3. genres_exploded.csv  → {len(genres_exploded):,} filas × {len(genres_exploded.columns)} cols")

    print("\n🔑 Columnas clave — Steam:")
    steam_key_cols = ['name', 'year', 'price', 'price_category', 'is_free',
                      'primary_genre', 'owners_midpoint', 'popularity_tier',
                      'positive', 'negative', 'review_ratio', 'pct_pos_total',
                      'average_playtime_forever', 'playtime_hours', 'peak_ccu',
                      'metacritic_score', 'has_metacritic', 'num_languages',
                      'num_screenshots', 'num_movies', 'sentiment_change']
    for col in steam_key_cols:
        if col in steam_clean.columns:
            dtype = steam_clean[col].dtype
            nulls = steam_clean[col].isnull().sum()
            print(f"   • {col:<30} {str(dtype):<12} nulls={nulls:,}")

    print("\n🔑 Columnas clave — Sales:")
    sales_key_cols = ['title', 'console', 'console_full', 'console_generation',
                      'console_manufacturer', 'genre', 'publisher', 'developer',
                      'critic_score', 'total_sales', 'na_sales', 'jp_sales',
                      'pal_sales', 'other_sales', 'dominant_region', 'year']
    for col in sales_key_cols:
        if col in sales_clean.columns:
            dtype = sales_clean[col].dtype
            nulls = sales_clean[col].isnull().sum()
            print(f"   • {col:<30} {str(dtype):<12} nulls={nulls:,}")

    print("\n✅ Fase 1 completada exitosamente!")
    print("   Próximo paso: ejecutar 02_analisis_mercado_steam.py")

    return steam_clean, sales_clean


if __name__ == '__main__':
    steam_clean, sales_clean = main()
