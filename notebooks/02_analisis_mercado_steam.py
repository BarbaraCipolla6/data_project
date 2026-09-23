import os
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

matplotlib.use('Agg')
sns.set_theme(style="whitegrid")

# Fix for paths when running from different locations
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_connection import query_to_dataframe

FIGURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output', 'figures'))
os.makedirs(FIGURES_DIR, exist_ok=True)

def main():
    print("Iniciando Fase 2A: Análisis del Mercado Digital (Steam)...")
    
    # 1. Juegos por año
    query_juegos_ano = """
        SELECT year, COUNT(*) AS juegos
        FROM steam_games
        WHERE year IS NOT NULL AND year >= 1997 AND year <= 2024
        GROUP BY year
        ORDER BY year
    """
    print(f"1. Juegos por año\n{query_juegos_ano}")
    df_juegos_ano = query_to_dataframe(query_juegos_ano)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df_juegos_ano, x='year', y='juegos', color='steelblue', ax=ax)
    plt.title('Cantidad de Juegos Lanzados en Steam por Año', fontsize=14)
    plt.xlabel('Año', fontsize=12)
    plt.ylabel('Cantidad de Juegos', fontsize=12)
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_01_juegos_por_ano.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 2. Crecimiento acumulado
    query_crecimiento = """
        SELECT year, 
               SUM(COUNT(*)) OVER (ORDER BY year) as acumulado
        FROM steam_games
        WHERE year IS NOT NULL AND year >= 1997 AND year <= 2024
        GROUP BY year
        ORDER BY year
    """
    print(f"2. Crecimiento acumulado\n{query_crecimiento}")
    df_crecimiento = query_to_dataframe(query_crecimiento)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=df_crecimiento, x='year', y='acumulado', marker='o', color='darkorange', ax=ax)
    plt.title('Crecimiento Acumulado de Juegos en Steam', fontsize=14)
    plt.xlabel('Año', fontsize=12)
    plt.ylabel('Juegos Acumulados', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_02_crecimiento_acumulado.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 3. Estacionalidad por mes
    query_mes = """
        SELECT month, COUNT(*) AS juegos
        FROM steam_games
        WHERE month IS NOT NULL
        GROUP BY month
        ORDER BY month
    """
    print(f"3. Estacionalidad por mes\n{query_mes}")
    df_mes = query_to_dataframe(query_mes)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df_mes, x='month', y='juegos', color='seagreen', ax=ax)
    plt.title('Estacionalidad: Lanzamientos por Mes en Steam', fontsize=14)
    plt.xlabel('Mes', fontsize=12)
    plt.ylabel('Cantidad de Juegos', fontsize=12)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_03_estacionalidad_lanzamientos.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 4. Distribución de precios
    query_precio = """
        SELECT price
        FROM steam_games
        WHERE price IS NOT NULL AND price <= 60 AND is_free = 0
    """
    print(f"4. Distribución de precios\n{query_precio}")
    df_precio = query_to_dataframe(query_precio)
    
    precios = df_precio['price'].values
    mean_price = np.mean(precios)
    median_price = np.median(precios)
    std_price = np.std(precios)
    
    # Calculate skewness with formula using numpy
    n = len(precios)
    mean_diff = precios - mean_price
    skewness = (np.sum(mean_diff**3) / n) / (std_price**3)
    
    p25 = np.percentile(precios, 25)
    p75 = np.percentile(precios, 75)
    
    print(f"Estadísticas de precios (<= $60): Media={mean_price:.2f}, Mediana={median_price:.2f}, Desviación={std_price:.2f}, Skewness={skewness:.2f}")
    print(f"Percentiles: 25%={p25:.2f}, 75%={p75:.2f}")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df_precio['price'], bins=30, kde=True, color='purple', ax=ax)
    plt.axvline(mean_price, color='red', linestyle='--', label=f'Media: ${mean_price:.2f}')
    plt.axvline(median_price, color='green', linestyle='-', label=f'Mediana: ${median_price:.2f}')
    plt.title('Distribución de Precios en Steam (hasta $60)', fontsize=14)
    plt.xlabel('Precio ($)', fontsize=12)
    plt.ylabel('Frecuencia', fontsize=12)
    plt.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_04_distribucion_precios.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 5. Evolución del precio medio por año
    query_precio_ano = """
        SELECT year, price
        FROM steam_games
        WHERE year IS NOT NULL AND year >= 2005 AND price IS NOT NULL AND is_free = 0
    """
    print(f"5. Evolución del precio medio\n{query_precio_ano}")
    df_precio_ano = query_to_dataframe(query_precio_ano)
    
    # Calculate mean per year using numpy
    years = np.sort(df_precio_ano['year'].unique())
    mean_prices = [np.mean(df_precio_ano[df_precio_ano['year'] == y]['price']) for y in years]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(x=years, y=mean_prices, marker='s', color='crimson', ax=ax)
    plt.title('Evolución del Precio Medio de Lanzamiento por Año', fontsize=14)
    plt.xlabel('Año', fontsize=12)
    plt.ylabel('Precio Medio ($)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_05_evolucion_precio.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 6. Proporción Free vs Paid
    query_free_paid = """
        SELECT year, is_free, COUNT(*) AS cantidad
        FROM steam_games
        WHERE year IS NOT NULL AND year >= 2005
        GROUP BY year, is_free
    """
    print(f"6. Proporción Free vs Paid\n{query_free_paid}")
    df_free_paid = query_to_dataframe(query_free_paid)
    
    pivot_fp = df_free_paid.pivot(index='year', columns='is_free', values='cantidad').fillna(0)
    pivot_fp.columns = ['Pago', 'Gratis']
    
    # Calculate percentages
    total = pivot_fp['Pago'] + pivot_fp['Gratis']
    pivot_fp_pct = pivot_fp.copy()
    pivot_fp_pct['Pago'] = (pivot_fp['Pago'] / total) * 100
    pivot_fp_pct['Gratis'] = (pivot_fp['Gratis'] / total) * 100
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.stackplot(pivot_fp_pct.index, pivot_fp_pct['Gratis'], pivot_fp_pct['Pago'], labels=['Gratis', 'Pago'], colors=['lightgreen', 'royalblue'], alpha=0.8)
    plt.title('Evolución de la Proporción de Juegos Gratis vs. de Pago', fontsize=14)
    plt.xlabel('Año', fontsize=12)
    plt.ylabel('Porcentaje (%)', fontsize=12)
    plt.legend(loc='upper left')
    plt.margins(x=0, y=0)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_06_proporcion_free_paid.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 7. Precio por género
    query_generos_precio = """
        SELECT g.genre_name, sg.price
        FROM steam_games sg
        JOIN steam_game_genres sgg ON sg.appid = sgg.appid
        JOIN genres g ON sgg.genre_id = g.genre_id
        WHERE sg.price IS NOT NULL AND sg.is_free = 0 AND sg.price <= 100
        AND g.genre_name IN (
            SELECT genre_name FROM (
                SELECT g2.genre_name, COUNT(*) as cnt
                FROM steam_game_genres sgg2
                JOIN genres g2 ON sgg2.genre_id = g2.genre_id
                GROUP BY g2.genre_name
                ORDER BY cnt DESC
                LIMIT 15
            ) as top_genres
        )
    """
    print(f"7. Precio por género\n{query_generos_precio}")
    df_gen_precio = query_to_dataframe(query_generos_precio)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.boxplot(data=df_gen_precio, x='price', y='genre_name', hue='genre_name', legend=False, ax=ax)
    plt.title('Distribución de Precios por Género (Top 15)', fontsize=14)
    plt.xlabel('Precio ($)', fontsize=12)
    plt.ylabel('Género', fontsize=12)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_07_precio_por_genero.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 8. Distribución de plataformas
    query_plats = """
        SELECT 
            SUM(windows) as Windows,
            SUM(mac) as Mac,
            SUM(linux) as Linux
        FROM steam_games
    """
    print(f"8. Distribución de plataformas\n{query_plats}")
    df_plats = query_to_dataframe(query_plats)
    
    plats = ['Windows', 'Mac', 'Linux']
    counts = [df_plats.iloc[0]['Windows'], df_plats.iloc[0]['Mac'], df_plats.iloc[0]['Linux']]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    plt.pie(counts, labels=plats, autopct='%1.1f%%', startangle=90, colors=['#0078D7', '#A2AAAD', '#FCC624'])
    plt.title('Distribución de Soporte por Plataforma en Steam', fontsize=14)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_08_distribucion_plataformas.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 9. Evolución de multiplataforma
    query_multi = """
        SELECT 
            year,
            SUM(CASE WHEN windows=1 AND mac=0 AND linux=0 THEN 1 ELSE 0 END) as solo_windows,
            SUM(CASE WHEN mac=1 OR linux=1 THEN 1 ELSE 0 END) as multiplataforma
        FROM steam_games
        WHERE year IS NOT NULL AND year >= 2008
        GROUP BY year
        ORDER BY year
    """
    print(f"9. Evolución de multiplataforma\n{query_multi}")
    df_multi = query_to_dataframe(query_multi)
    
    total = df_multi['solo_windows'] + df_multi['multiplataforma']
    df_multi['pct_solo_windows'] = (df_multi['solo_windows'] / total) * 100
    df_multi['pct_multiplataforma'] = (df_multi['multiplataforma'] / total) * 100
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.stackplot(df_multi['year'], df_multi['pct_solo_windows'], df_multi['pct_multiplataforma'], 
                labels=['Solo Windows', 'Multiplataforma (Mac/Linux)'], 
                colors=['skyblue', 'salmon'], alpha=0.8)
    plt.title('Evolución del Soporte Multiplataforma por Año', fontsize=14)
    plt.xlabel('Año', fontsize=12)
    plt.ylabel('Porcentaje (%)', fontsize=12)
    plt.legend(loc='lower left')
    plt.margins(x=0, y=0)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_09_evolucion_multiplataforma.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 10. Top publishers count
    query_pub_count = """
        SELECT p.publisher_name, COUNT(*) as juegos
        FROM steam_game_publishers sgp
        JOIN publishers p ON sgp.publisher_id = p.publisher_id
        GROUP BY p.publisher_name
        ORDER BY juegos DESC
        LIMIT 20
    """
    print(f"10. Top publishers count\n{query_pub_count}")
    df_pub_count = query_to_dataframe(query_pub_count)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.barplot(data=df_pub_count, x='juegos', y='publisher_name', hue='publisher_name', legend=False, ax=ax, palette='viridis')
    plt.title('Top 20 Publishers por Cantidad de Juegos en Steam', fontsize=14)
    plt.xlabel('Cantidad de Juegos', fontsize=12)
    plt.ylabel('Publisher', fontsize=12)
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_10_top_publishers_count.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # 11. Top publishers owners
    query_pub_own = """
        SELECT p.publisher_name, SUM(sg.owners_midpoint) as total_owners
        FROM steam_game_publishers sgp
        JOIN publishers p ON sgp.publisher_id = p.publisher_id
        JOIN steam_games sg ON sgp.appid = sg.appid
        GROUP BY p.publisher_name
        ORDER BY total_owners DESC
        LIMIT 20
    """
    print(f"11. Top publishers owners\n{query_pub_own}")
    df_pub_own = query_to_dataframe(query_pub_own)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.barplot(data=df_pub_own, x='total_owners', y='publisher_name', hue='publisher_name', legend=False, ax=ax, palette='magma')
    plt.title('Top 20 Publishers por Jugadores Estimados (Owners)', fontsize=14)
    plt.xlabel('Total Owners (Estimado)', fontsize=12)
    plt.ylabel('Publisher', fontsize=12)
    
    # Formatear eje x a millones
    def millions_formatter(x, pos):
        return f'{x / 1e6:.0f}M'
    ax.xaxis.set_major_formatter(plt.FuncFormatter(millions_formatter))
    
    plt.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '02_11_top_publishers_owners.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    print("Fase 2A completada. Gráficos guardados en:", FIGURES_DIR)

if __name__ == "__main__":
    main()
