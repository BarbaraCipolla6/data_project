"""
transformations.py — Funciones de transformación y feature engineering.

Contiene funciones para crear nuevas columnas derivadas, explotar géneros,
crear matrices de co-ocurrencia, calcular índices compuestos, y realizar
el merge cruzado entre los datasets de Steam y Sales.
"""

import numpy as np
import pandas as pd
from typing import Optional


# ============================================================================
# FEATURE ENGINEERING — STEAM
# ============================================================================

def add_temporal_features(df: pd.DataFrame, date_col: str = 'release_date') -> pd.DataFrame:
    """Agrega columnas temporales derivadas de la fecha de lanzamiento.

    Args:
        df: DataFrame con columna de fecha.
        date_col: Nombre de la columna de fecha.

    Returns:
        DataFrame con columnas 'year', 'month', 'decade' agregadas.

    Example:
        >>> df = add_temporal_features(df, 'release_date')
        >>> df[['year', 'month', 'decade']].head()
    """
    df = df.copy()
    dt = pd.to_datetime(df[date_col], errors='coerce')
    df['year'] = dt.dt.year.astype('Int64')
    df['month'] = dt.dt.month.astype('Int64')
    df['decade'] = (df['year'] // 10 * 10).astype('Int64')
    df['release_date_dt'] = dt
    return df


def add_review_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega métricas de reviews derivadas.

    Calcula el ratio de reviews positivas, total de reviews calculado,
    y la diferencia entre reviews recientes y totales.

    Args:
        df: DataFrame con columnas 'positive', 'negative', 'pct_pos_total', 'pct_pos_recent'.

    Returns:
        DataFrame con columnas de review features agregadas.
    """
    df = df.copy()

    total = df['positive'] + df['negative']
    # Evitar división por cero
    df['review_ratio'] = np.where(total > 0, df['positive'] / total, np.nan)
    df['total_reviews_calc'] = total
    df['sentiment_change'] = df['pct_pos_recent'] - df['pct_pos_total']

    return df


def add_product_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega métricas de producto derivadas.

    Calcula features como cantidad de géneros, idiomas, screenshots,
    trailers, categoría de precio, y si el juego es gratuito.

    Args:
        df: DataFrame con columnas de producto de Steam.

    Returns:
        DataFrame con features de producto agregadas.
    """
    df = df.copy()

    # Contar elementos en columnas de listas (ya parseadas)
    df['num_genres'] = df['genres'].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    )
    df['primary_genre'] = df['genres'].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else 'Unknown'
    )
    df['num_languages'] = df['supported_languages'].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    )

    # Contar screenshots y movies (si son listas)
    for col, new_col in [('screenshots', 'num_screenshots'), ('movies', 'num_movies')]:
        if col in df.columns:
            df[new_col] = df[col].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )

    # Categoría de precio
    df['is_free'] = df['price'] == 0
    df['price_category'] = pd.cut(
        df['price'],
        bins=[-0.01, 0, 4.99, 14.99, 29.99, float('inf')],
        labels=['Free', 'Budget', 'Mid', 'Premium', 'AAA']
    )

    # Metacritic
    df['has_metacritic'] = df['metacritic_score'] > 0

    # Playtime en horas
    df['playtime_hours'] = df['average_playtime_forever'] / 60

    # Longitud de descripción
    if 'short_description' in df.columns:
        df['description_length'] = df['short_description'].fillna('').str.len()

    return df


def add_owner_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega features derivadas de estimated_owners.

    Calcula el midpoint, y crea una categoría de popularidad.

    Args:
        df: DataFrame con columna 'owners_min', 'owners_max', 'owners_midpoint'.

    Returns:
        DataFrame con features de popularidad.
    """
    df = df.copy()

    # Categoría de popularidad basada en owners_midpoint
    bins = [0, 10000, 35000, 75000, 350000, 1500000, float('inf')]
    labels = ['Nicho', 'Indie', 'Mid-tier', 'Popular', 'Hit', 'Blockbuster']
    df['popularity_tier'] = pd.cut(
        df['owners_midpoint'], bins=bins, labels=labels
    )

    return df


# ============================================================================
# FEATURE ENGINEERING — SALES
# ============================================================================

def add_sales_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega features derivadas al dataset de ventas.

    Calcula participación regional, región dominante, y features temporales.

    Args:
        df: DataFrame de ventas con columnas de sales regionales.

    Returns:
        DataFrame con features de ventas agregadas.
    """
    df = df.copy()

    # Participación regional (solo donde hay total_sales)
    has_total = df['total_sales'] > 0
    for region in ['na_sales', 'jp_sales', 'pal_sales', 'other_sales']:
        share_col = region.replace('_sales', '_share')
        df[share_col] = np.where(
            has_total,
            df[region] / df['total_sales'],
            np.nan
        )

    # Región dominante
    region_cols = ['na_sales', 'jp_sales', 'pal_sales', 'other_sales']
    region_labels = ['NA', 'JP', 'PAL', 'Other']

    def get_dominant_region(row):
        values = [row.get(c, 0) for c in region_cols]
        if all(pd.isna(v) or v == 0 for v in values):
            return 'Unknown'
        values = [0 if pd.isna(v) else v for v in values]
        return region_labels[np.argmax(values)]

    df['dominant_region'] = df.apply(get_dominant_region, axis=1)

    return df


# ============================================================================
# EXPLOSIÓN DE GÉNEROS
# ============================================================================

def explode_genres(df: pd.DataFrame, genre_col: str = 'genres',
                   id_cols: Optional[list] = None) -> pd.DataFrame:
    """Crea un DataFrame con una fila por género por juego.

    Args:
        df: DataFrame con columna de géneros (lista).
        genre_col: Nombre de la columna de géneros.
        id_cols: Columnas a mantener además del género. Si None, usa las más comunes.

    Returns:
        DataFrame con una fila por cada combinación juego-género.

    Example:
        >>> genres_df = explode_genres(df)
        >>> genres_df.groupby('genre')['owners_midpoint'].mean()
    """
    if id_cols is None:
        # Columnas por defecto relevantes para análisis
        available = df.columns.tolist()
        default_cols = ['appid', 'name', 'year', 'price', 'price_category',
                        'owners_midpoint', 'popularity_tier', 'positive', 'negative',
                        'review_ratio', 'pct_pos_total', 'average_playtime_forever',
                        'peak_ccu', 'metacritic_score', 'has_metacritic']
        id_cols = [c for c in default_cols if c in available]

    df_subset = df[id_cols + [genre_col]].copy()
    df_exploded = df_subset.explode(genre_col).rename(columns={genre_col: 'genre'})
    df_exploded = df_exploded.dropna(subset=['genre'])
    df_exploded['genre'] = df_exploded['genre'].str.strip()

    return df_exploded


# ============================================================================
# MATRIZ DE CO-OCURRENCIA DE GÉNEROS
# ============================================================================

def create_genre_cooccurrence(df: pd.DataFrame, genre_col: str = 'genres',
                               top_n: int = 15) -> pd.DataFrame:
    """Crea una matriz de co-ocurrencia de géneros.

    Args:
        df: DataFrame con columna de géneros (lista).
        genre_col: Nombre de la columna de géneros.
        top_n: Número de géneros top a incluir.

    Returns:
        DataFrame con la matriz de co-ocurrencia (genre × genre).
    """
    # Obtener top N géneros
    exploded = df.explode(genre_col)[genre_col].dropna()
    top_genres = exploded.value_counts().head(top_n).index.tolist()

    # Crear matriz binaria
    genre_matrix = pd.DataFrame(index=df.index)
    for genre in top_genres:
        genre_matrix[genre] = df[genre_col].apply(
            lambda x: genre in x if isinstance(x, list) else False
        ).astype(int)

    # Matriz de co-ocurrencia = producto matricial
    cooccurrence = genre_matrix.T.dot(genre_matrix)

    return cooccurrence


# ============================================================================
# TOP TAGS
# ============================================================================

def extract_top_tags(tags_dict: dict, n: int = 5) -> list:
    """Extrae los N tags con más votos de un diccionario de tags.

    Args:
        tags_dict: Diccionario {tag_name: vote_count}.
        n: Número de tags top a extraer.

    Returns:
        Lista de los N tags más votados.

    Example:
        >>> extract_top_tags({'FPS': 90857, 'Shooter': 65397, 'Action': 47512}, n=2)
        ['FPS', 'Shooter']
    """
    if not isinstance(tags_dict, dict) or len(tags_dict) == 0:
        return []
    sorted_tags = sorted(tags_dict.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in sorted_tags[:n]]


# ============================================================================
# MERGE CRUZADO STEAM × SALES
# ============================================================================

def normalize_title(title: str) -> str:
    """Normaliza un título de juego para matching.

    Convierte a minúsculas, elimina caracteres especiales,
    y normaliza espacios.

    Args:
        title: Título original del juego.

    Returns:
        Título normalizado.
    """
    if not isinstance(title, str):
        return ''
    import re
    title = title.lower().strip()
    # Eliminar contenido entre paréntesis (ej: "(2020 Edition)")
    title = re.sub(r'\([^)]*\)', '', title)
    # Eliminar caracteres especiales excepto espacios
    title = re.sub(r'[^a-z0-9\s]', '', title)
    # Normalizar espacios múltiples
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def merge_steam_sales(steam_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    """Realiza un merge entre los datasets de Steam y Sales por título.

    Usa matching por título normalizado. Solo retorna juegos que
    aparecen en AMBOS datasets.

    Args:
        steam_df: DataFrame limpio de Steam.
        sales_df: DataFrame limpio de Sales.

    Returns:
        DataFrame con datos combinados de ambos datasets.
    """
    print("🔗 Realizando merge cruzado Steam × Sales...")

    # Normalizar títulos
    steam_copy = steam_df.copy()
    sales_copy = sales_df.copy()
    steam_copy['title_norm'] = steam_copy['name'].apply(normalize_title)
    sales_copy['title_norm'] = sales_copy['title'].apply(normalize_title)

    # Filtrar ventas solo de PC para un merge más limpio con Steam
    sales_pc = sales_copy[sales_copy['console'] == 'PC'].copy()

    # Merge por título normalizado
    merged = steam_copy.merge(
        sales_pc,
        on='title_norm',
        how='inner',
        suffixes=('_steam', '_sales')
    )

    # Eliminar duplicados (mantener el de mayor total_sales)
    merged = merged.sort_values('total_sales', ascending=False)
    merged = merged.drop_duplicates(subset=['title_norm'], keep='first')

    print(f"   ✅ Juegos matcheados: {len(merged):,}")
    print(f"   📊 De {len(steam_copy):,} Steam + {len(sales_pc):,} Sales (PC)")

    return merged
