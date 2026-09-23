"""
01_limpieza_carga_mysql.py — ETL: CSV → Python (limpieza) → MySQL
Pipeline principal del proyecto.

Flujo:
1. Lee los CSVs crudos originales
2. Limpia con Python (funciones de utils/cleaning.py)
3. Crea el schema en MySQL (sql/schema.sql)
4. Inserta los datos limpios en las tablas normalizadas
5. Valida los conteos
"""

import sys
import os
import ast
import warnings

# Fix encoding para Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import mysql.connector

# Setup de paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from utils.db_connection import get_connection, execute_query, execute_many, DB_NAME
from utils.cleaning import (
    parse_string_list, parse_tag_dict, parse_owner_range,
    categorize_price, standardize_console_name,
    categorize_console_generation, get_console_manufacturer
)

RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
SQL_DIR = os.path.join(PROJECT_ROOT, 'sql')


def safe_val(val):
    """Convierte valores NaN/NaT a None para MySQL."""
    if pd.isna(val):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    return val


def create_database_and_schema():
    """Crea las tablas usando schema.sql vía la conexión de mysql-connector (compatible con local y Aiven)."""
    print("\n[1/5] Creando base de datos y schema...")

    schema_path = os.path.join(SQL_DIR, 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Separar bloques SQL por punto y coma (;)
    statements = sql_content.split(';')
    
    conn = get_connection(use_database=True)
    cursor = conn.cursor()

    created_tables = []
    for stmt in statements:
        # Limpiar espacios y comentarios
        lines = [line.strip() for line in stmt.split('\n') if line.strip() and not line.strip().startswith('--')]
        clean_stmt = ' '.join(lines).strip()
        
        if not clean_stmt:
            continue
        
        # Ignorar comandos de creación/cambio de DB que pueden fallar en la nube
        upper_stmt = clean_stmt.upper()
        if upper_stmt.startswith('CREATE DATABASE') or upper_stmt.startswith('USE '):
            continue

        try:
            cursor.execute(clean_stmt)
            if 'CREATE TABLE' in upper_stmt:
                table_name = clean_stmt.split('EXISTS')[1].split('(')[0].strip() if 'EXISTS' in upper_stmt else clean_stmt.split('TABLE')[1].split('(')[0].strip()
                created_tables.append(table_name)
        except Exception as e:
            print(f"  Advertencia SQL: {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print("  Tablas en schema:")
    for t in created_tables:
        print(f"    • {t}")
    print("  ✅ Schema verificado y listo exitosamente")


def load_and_clean_steam():
    """Carga y limpia el dataset de Steam desde el CSV crudo."""
    print("\n[2/5] Cargando y limpiando dataset de Steam...")

    raw_path = os.path.join(RAW_DIR, 'games_march2025_cleaned.csv')
    df = pd.read_csv(raw_path, low_memory=False)
    print(f"  Cargadas {len(df):,} filas crudas")

    # --- Limpieza con Python ---

    # Parsear columnas de listas (string repr → Python list)
    for col in ['genres', 'publishers', 'developers']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: parse_string_list(x) if isinstance(x, str) else [])

    # Parsear tags (string repr de dict)
    if 'tags' in df.columns:
        df['tags'] = df['tags'].apply(lambda x: parse_tag_dict(x) if isinstance(x, str) else {})

    # Parsear owners
    if 'estimated_owners' in df.columns:
        owner_parsed = df['estimated_owners'].apply(parse_owner_range)
        df['owners_min'] = owner_parsed.apply(lambda x: x[0] if x else None)
        df['owners_max'] = owner_parsed.apply(lambda x: x[1] if x else None)
        df['owners_midpoint'] = owner_parsed.apply(lambda x: x[2] if x else None)

    # Extraer año/mes de release_date
    if 'release_date' in df.columns:
        df['release_date_dt'] = pd.to_datetime(df['release_date'], errors='coerce')
        df['year'] = df['release_date_dt'].dt.year
        df['month'] = df['release_date_dt'].dt.month

    # Features derivadas
    df['is_free'] = (df['price'] == 0) if 'price' in df.columns else False
    df['price_category'] = df['price'].apply(categorize_price) if 'price' in df.columns else 'Unknown'
    df['has_metacritic'] = df['metacritic_score'].notna() & (df['metacritic_score'] > 0) if 'metacritic_score' in df.columns else False
    df['primary_genre'] = df['genres'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
    df['playtime_hours'] = df['average_playtime_forever'] / 60 if 'average_playtime_forever' in df.columns else 0

    # Num languages / screenshots / movies
    if 'supported_languages' in df.columns:
        df['num_languages'] = df['supported_languages'].apply(
            lambda x: len(parse_string_list(x)) if isinstance(x, str) else 1
        )
    if 'screenshots' in df.columns:
        df['num_screenshots'] = df['screenshots'].apply(
            lambda x: len(parse_string_list(x)) if isinstance(x, str) else 0
        )
    elif 'num_screenshots' not in df.columns:
        df['num_screenshots'] = 0

    if 'movies' in df.columns:
        df['num_movies'] = df['movies'].apply(
            lambda x: len(parse_string_list(x)) if isinstance(x, str) else 0
        )
    elif 'num_movies' not in df.columns:
        df['num_movies'] = 0

    # Review ratio
    total_reviews = df.get('positive', 0) + df.get('negative', 0)
    if isinstance(total_reviews, pd.Series):
        df['num_reviews_total'] = total_reviews.astype(int)
        df['review_ratio'] = np.where(total_reviews > 0, df['positive'] / total_reviews * 100, None)
    df['num_reviews_recent'] = df.get('num_reviews_recent', 0)

    # Popularity tier
    def get_popularity_tier(owners):
        if pd.isna(owners) or owners == 0:
            return None
        elif owners < 5000:
            return 'Nicho'
        elif owners < 50000:
            return 'Pequeño'
        elif owners < 500000:
            return 'Medio'
        elif owners < 5000000:
            return 'Popular'
        else:
            return 'Masivo'

    df['popularity_tier'] = df['owners_midpoint'].apply(get_popularity_tier)

    print(f"  ✅ Limpieza completada: {len(df):,} filas")
    return df


def load_and_clean_sales():
    """Carga y limpia el dataset de ventas de consolas desde el CSV crudo."""
    print("\n[3/5] Cargando y limpiando dataset de ventas...")

    raw_path = os.path.join(RAW_DIR, 'Video Games Sales (1980-2024) - Raw.csv')
    df = pd.read_csv(raw_path, low_memory=False)
    print(f"  Cargadas {len(df):,} filas crudas")

    # --- Limpieza con Python ---

    # Estandarizar nombres de consola
    if 'console' in df.columns:
        df['console_full'] = df['console'].apply(standardize_console_name)
        df['console_generation'] = df['console'].apply(categorize_console_generation)
        df['console_manufacturer'] = df['console'].apply(get_console_manufacturer)

    # Extraer año de release_date
    if 'release_date' in df.columns:
        df['release_date_dt'] = pd.to_datetime(df['release_date'], errors='coerce')
        df['year'] = df['release_date_dt'].dt.year

    # Decade
    df['decade'] = df['year'].apply(lambda x: f"{int(x // 10 * 10)}s" if pd.notna(x) else None)

    # Shares regionales
    for region in ['na_sales', 'jp_sales', 'pal_sales', 'other_sales']:
        col = region.replace('_sales', '_share')
        df[col] = np.where(
            df['total_sales'].notna() & (df['total_sales'] > 0),
            df[region] / df['total_sales'],
            None
        )

    # Región dominante
    regions = {'NA': 'na_sales', 'JP': 'jp_sales', 'PAL': 'pal_sales', 'Other': 'other_sales'}
    def get_dominant(row):
        vals = {k: row.get(v, 0) or 0 for k, v in regions.items()}
        return max(vals, key=vals.get) if any(v > 0 for v in vals.values()) else None
    df['dominant_region'] = df.apply(get_dominant, axis=1)

    print(f"  ✅ Limpieza completada: {len(df):,} filas")
    return df


def insert_steam_data(df_steam):
    """Inserta datos de Steam en las tablas normalizadas de MySQL."""
    print("\n[4/5] Insertando datos de Steam en MySQL...")

    conn = get_connection(use_database=True)
    cursor = conn.cursor()

    # --- 4a: Insertar géneros únicos ---
    all_genres = set()
    for genres_list in df_steam['genres']:
        if isinstance(genres_list, list):
            all_genres.update(genres_list)

    # También géneros del dataset de ventas (se insertan después)
    genre_tuples = [(g,) for g in sorted(all_genres) if g]
    cursor.executemany(
        "INSERT IGNORE INTO genres (genre_name) VALUES (%s)",
        genre_tuples
    )
    conn.commit()
    print(f"  Géneros insertados: {len(genre_tuples)}")

    # Obtener mapping genre_name → genre_id
    cursor.execute("SELECT genre_id, genre_name FROM genres")
    genre_map = {name: gid for gid, name in cursor.fetchall()}

    # --- 4b: Insertar publishers únicos ---
    all_publishers = set()
    for pub_list in df_steam['publishers']:
        if isinstance(pub_list, list):
            all_publishers.update(pub_list)

    pub_tuples = [(p,) for p in sorted(all_publishers) if p]
    cursor.executemany(
        "INSERT IGNORE INTO publishers (publisher_name) VALUES (%s)",
        pub_tuples
    )
    conn.commit()
    print(f"  Publishers insertados: {len(pub_tuples)}")

    cursor.execute("SELECT publisher_id, publisher_name FROM publishers")
    pub_map = {name: pid for pid, name in cursor.fetchall()}

    # --- 4c: Insertar steam_games ---
    print("  Insertando steam_games (puede tardar unos segundos)...")
    game_cols = [
        'appid', 'name', 'year', 'month', 'price', 'price_category', 'is_free',
        'owners_min', 'owners_max', 'owners_midpoint', 'popularity_tier',
        'positive', 'negative', 'review_ratio', 'pct_pos_total', 'pct_pos_recent',
        'num_reviews_total', 'num_reviews_recent', 'average_playtime_forever',
        'playtime_hours', 'peak_ccu', 'metacritic_score', 'has_metacritic',
        'num_languages', 'num_screenshots', 'num_movies', 'dlc_count',
        'achievements', 'recommendations', 'windows', 'mac', 'linux', 'primary_genre'
    ]

    insert_sql = f"""
        INSERT IGNORE INTO steam_games
        ({', '.join(game_cols)})
        VALUES ({', '.join(['%s'] * len(game_cols))})
    """

    batch_size = 5000
    total_inserted = 0

    for start in range(0, len(df_steam), batch_size):
        batch = df_steam.iloc[start:start + batch_size]
        rows = []
        for _, row in batch.iterrows():
            vals = tuple(safe_val(row.get(col)) for col in game_cols)
            rows.append(vals)
        cursor.executemany(insert_sql, rows)
        conn.commit()
        total_inserted += len(rows)
        print(f"    Progreso: {total_inserted:,}/{len(df_steam):,}", end='\r')

    print(f"\n  ✅ steam_games insertados: {total_inserted:,}")

    # --- 4d: Insertar relaciones M:N ---
    print("  Insertando relaciones género-juego...")
    genre_rows = []
    for _, row in df_steam.iterrows():
        if isinstance(row['genres'], list):
            for genre in row['genres']:
                if genre in genre_map:
                    genre_rows.append((int(row['appid']), genre_map[genre]))

    for start in range(0, len(genre_rows), 10000):
        batch = genre_rows[start:start + 10000]
        cursor.executemany(
            "INSERT IGNORE INTO steam_game_genres (appid, genre_id) VALUES (%s, %s)",
            batch
        )
        conn.commit()
    print(f"  ✅ steam_game_genres: {len(genre_rows):,} relaciones")

    # Tags
    print("  Insertando tags...")
    tag_rows = []
    for _, row in df_steam.iterrows():
        if isinstance(row['tags'], dict):
            for tag_name, votes in row['tags'].items():
                tag_rows.append((int(row['appid']), str(tag_name)[:200], int(votes)))

    for start in range(0, len(tag_rows), 10000):
        batch = tag_rows[start:start + 10000]
        cursor.executemany(
            "INSERT IGNORE INTO steam_game_tags (appid, tag_name, tag_votes) VALUES (%s, %s, %s)",
            batch
        )
        conn.commit()
    print(f"  ✅ steam_game_tags: {len(tag_rows):,} registros")

    # Publishers
    print("  Insertando publishers-juego...")
    pub_rows = []
    for _, row in df_steam.iterrows():
        if isinstance(row['publishers'], list):
            for pub in row['publishers']:
                if pub in pub_map:
                    pub_rows.append((int(row['appid']), pub_map[pub]))

    for start in range(0, len(pub_rows), 10000):
        batch = pub_rows[start:start + 10000]
        cursor.executemany(
            "INSERT IGNORE INTO steam_game_publishers (appid, publisher_id) VALUES (%s, %s)",
            batch
        )
        conn.commit()
    print(f"  ✅ steam_game_publishers: {len(pub_rows):,} relaciones")

    # Developers
    print("  Insertando developers-juego...")
    dev_rows = []
    for _, row in df_steam.iterrows():
        if isinstance(row['developers'], list):
            for dev in row['developers']:
                dev_rows.append((int(row['appid']), str(dev)[:255]))

    for start in range(0, len(dev_rows), 10000):
        batch = dev_rows[start:start + 10000]
        cursor.executemany(
            "INSERT IGNORE INTO steam_game_developers (appid, developer_name) VALUES (%s, %s)",
            batch
        )
        conn.commit()
    print(f"  ✅ steam_game_developers: {len(dev_rows):,} relaciones")

    cursor.close()
    conn.close()


def insert_sales_data(df_sales):
    """Inserta datos de ventas de consolas en MySQL."""
    print("\n[4b/5] Insertando datos de ventas en MySQL...")

    conn = get_connection(use_database=True)
    cursor = conn.cursor()

    # --- Insertar consolas únicas ---
    consoles_data = df_sales[['console', 'console_full', 'console_generation', 'console_manufacturer']].drop_duplicates(subset='console')
    console_tuples = [
        (row['console'], safe_val(row['console_full']),
         safe_val(row['console_generation']), safe_val(row['console_manufacturer']))
        for _, row in consoles_data.iterrows() if row['console']
    ]
    cursor.executemany(
        "INSERT IGNORE INTO consoles (console_abbrev, console_full, console_generation, console_manufacturer) VALUES (%s, %s, %s, %s)",
        console_tuples
    )
    conn.commit()
    print(f"  Consolas insertadas: {len(console_tuples)}")

    # Mapping console_abbrev → console_id
    cursor.execute("SELECT console_id, console_abbrev FROM consoles")
    console_map = {name: cid for cid, name in cursor.fetchall()}

    # Genre map
    cursor.execute("SELECT genre_id, genre_name FROM genres")
    genre_map = {name: gid for gid, name in cursor.fetchall()}

    # Insertar géneros de ventas que no existan aún
    sales_genres = set(df_sales['genre'].dropna().unique())
    new_genres = [(g,) for g in sales_genres if g not in genre_map]
    if new_genres:
        cursor.executemany("INSERT IGNORE INTO genres (genre_name) VALUES (%s)", new_genres)
        conn.commit()
        cursor.execute("SELECT genre_id, genre_name FROM genres")
        genre_map = {name: gid for gid, name in cursor.fetchall()}

    # --- Insertar console_games ---
    print("  Insertando console_games...")
    insert_sql = """
        INSERT INTO console_games
        (title, console_id, genre_id, publisher, developer,
         critic_score, total_sales, na_sales, jp_sales, pal_sales, other_sales,
         release_date, year, decade, dominant_region,
         na_share, jp_share, pal_share, other_share,
         console_generation, console_manufacturer)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    batch_size = 5000
    total_inserted = 0

    for start in range(0, len(df_sales), batch_size):
        batch = df_sales.iloc[start:start + batch_size]
        rows = []
        for _, row in batch.iterrows():
            # Parse release date
            rd = None
            if pd.notna(row.get('release_date_dt')):
                try:
                    rd = pd.Timestamp(row['release_date_dt']).strftime('%Y-%m-%d')
                except:
                    rd = None

            vals = (
                safe_val(row.get('title')),
                console_map.get(row.get('console')),
                genre_map.get(row.get('genre')),
                safe_val(row.get('publisher')),
                safe_val(row.get('developer')),
                safe_val(row.get('critic_score')),
                safe_val(row.get('total_sales')),
                safe_val(row.get('na_sales')),
                safe_val(row.get('jp_sales')),
                safe_val(row.get('pal_sales')),
                safe_val(row.get('other_sales')),
                rd,
                safe_val(row.get('year')),
                safe_val(row.get('decade')),
                safe_val(row.get('dominant_region')),
                safe_val(row.get('na_share')),
                safe_val(row.get('jp_share')),
                safe_val(row.get('pal_share')),
                safe_val(row.get('other_share')),
                safe_val(row.get('console_generation')),
                safe_val(row.get('console_manufacturer')),
            )
            rows.append(vals)

        cursor.executemany(insert_sql, rows)
        conn.commit()
        total_inserted += len(rows)
        print(f"    Progreso: {total_inserted:,}/{len(df_sales):,}", end='\r')

    print(f"\n  ✅ console_games insertados: {total_inserted:,}")
    cursor.close()
    conn.close()


def validate_data():
    """Valida los conteos en todas las tablas."""
    print("\n[5/5] Validando datos en MySQL...")

    conn = get_connection(use_database=True)
    cursor = conn.cursor()

    tables = ['genres', 'publishers', 'consoles', 'steam_games',
              'steam_game_genres', 'steam_game_tags',
              'steam_game_publishers', 'steam_game_developers',
              'console_games']

    print(f"\n{'='*55}")
    print(f"  {'Tabla':<30} {'Filas':>12}")
    print(f"{'='*55}")

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:<30} {count:>12,}")

    print(f"{'='*55}")

    cursor.close()
    conn.close()
    print("\n✅ ETL completado exitosamente: CSV → Python → MySQL")
    print("La base de datos está lista para consultas SQL.\n")


def main():
    print("=" * 60)
    print("  ETL: CSV → Python (limpieza) → MySQL")
    print("  Base de datos: videogame_market_analysis")
    print("=" * 60)

    # Paso 1: Crear schema
    create_database_and_schema()

    # Paso 2: Cargar y limpiar Steam
    df_steam = load_and_clean_steam()

    # Paso 3: Cargar y limpiar Sales
    df_sales = load_and_clean_sales()

    # Paso 4: Insertar en MySQL
    insert_steam_data(df_steam)
    insert_sales_data(df_sales)

    # Paso 5: Validar
    validate_data()


if __name__ == '__main__':
    main()
