import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar path para importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_connection import query_to_dataframe

# Directorio de figuras
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES_DIR = os.path.join(BASE_DIR, 'output', 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

sns.set_theme(style="whitegrid")

print("Iniciando Fase 2B: Análisis de Ventas Globales (Consolas)...")

# 1. 03_01_top20_juegos.png
sql_1 = """
SELECT cg.title, cg.total_sales, c.console_abbrev 
FROM console_games cg 
LEFT JOIN consoles c ON cg.console_id = c.console_id 
ORDER BY cg.total_sales DESC 
LIMIT 20
"""
print(f"Ejecutando consulta 1:\n{sql_1}")
df_1 = query_to_dataframe(sql_1)
if not df_1.empty:
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.barplot(data=df_1, x='total_sales', y='title', hue='console_abbrev', dodge=False, ax=ax)
    ax.set_title('Top 20 Juegos por Ventas Totales', fontsize=16)
    ax.set_xlabel('Ventas Totales (Millones)', fontsize=12)
    ax.set_ylabel('Juego', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_01_top20_juegos.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 2. 03_02_ventas_por_generacion.png
sql_2 = """
SELECT cg.console_generation, SUM(cg.total_sales) as total_sales
FROM console_games cg
WHERE cg.console_generation IS NOT NULL
GROUP BY cg.console_generation
ORDER BY cg.console_generation ASC
"""
print(f"Ejecutando consulta 2:\n{sql_2}")
df_2 = query_to_dataframe(sql_2)
if not df_2.empty:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df_2, x='console_generation', y='total_sales', hue='console_generation', legend=False, ax=ax, palette='viridis')
    ax.set_title('Ventas Totales por Generación de Consolas', fontsize=16)
    ax.set_xlabel('Generación', fontsize=12)
    ax.set_ylabel('Ventas Totales (Millones)', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_02_ventas_por_generacion.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 3. 03_03_cuota_mercado_fabricante.png
sql_3 = """
SELECT cg.console_manufacturer, SUM(cg.total_sales) as total_sales
FROM console_games cg
WHERE cg.console_manufacturer IS NOT NULL
GROUP BY cg.console_manufacturer
ORDER BY total_sales DESC
"""
print(f"Ejecutando consulta 3:\n{sql_3}")
df_3 = query_to_dataframe(sql_3)
if not df_3.empty:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df_3, x='console_manufacturer', y='total_sales', hue='console_manufacturer', legend=False, ax=ax, palette='magma')
    ax.set_title('Cuota de Mercado por Fabricante (Ventas Totales)', fontsize=16)
    ax.set_xlabel('Fabricante', fontsize=12)
    ax.set_ylabel('Ventas Totales (Millones)', fontsize=12)
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_03_cuota_mercado_fabricante.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 4. 03_04_top15_consolas.png
sql_4 = """
SELECT c.console_abbrev, SUM(cg.total_sales) as total_sales
FROM console_games cg
JOIN consoles c ON cg.console_id = c.console_id
GROUP BY c.console_abbrev
ORDER BY total_sales DESC
LIMIT 15
"""
print(f"Ejecutando consulta 4:\n{sql_4}")
df_4 = query_to_dataframe(sql_4)
if not df_4.empty:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df_4, x='console_abbrev', y='total_sales', hue='console_abbrev', legend=False, ax=ax, palette='rocket')
    ax.set_title('Top 15 Consolas por Ventas de Juegos', fontsize=16)
    ax.set_xlabel('Consola', fontsize=12)
    ax.set_ylabel('Ventas Totales (Millones)', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_04_top15_consolas.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 5. 03_05_ventas_por_region.png
sql_5 = """
SELECT 
    SUM(na_sales) as na_sales,
    SUM(jp_sales) as jp_sales,
    SUM(pal_sales) as pal_sales,
    SUM(other_sales) as other_sales
FROM console_games
"""
print(f"Ejecutando consulta 5:\n{sql_5}")
df_5 = query_to_dataframe(sql_5)
if not df_5.empty:
    sales_data = df_5.iloc[0]
    labels = ['Norteamérica (NA)', 'Japón (JP)', 'Europa/PAL', 'Otras Regiones']
    sizes = [sales_data['na_sales'], sales_data['jp_sales'], sales_data['pal_sales'], sales_data['other_sales']]
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, pctdistance=0.85, colors=sns.color_palette("pastel"))
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig.gca().add_artist(centre_circle)
    ax.set_title('Distribución de Ventas por Región', fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_05_ventas_por_region.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 6. 03_06_generos_por_region.png
sql_6 = """
SELECT 
    g.genre_name,
    AVG(cg.na_share) as na_share,
    AVG(cg.jp_share) as jp_share,
    AVG(cg.pal_share) as pal_share,
    AVG(cg.other_share) as other_share
FROM console_games cg
JOIN genres g ON cg.genre_id = g.genre_id
GROUP BY g.genre_name
"""
print(f"Ejecutando consulta 6:\n{sql_6}")
df_6 = query_to_dataframe(sql_6)
if not df_6.empty:
    df_6.set_index('genre_name', inplace=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(df_6, cmap='YlGnBu', annot=True, fmt=".2f", ax=ax)
    ax.set_title('Preferencia de Géneros por Región (Cuota Media %)', fontsize=16)
    ax.set_xlabel('Región', fontsize=12)
    ax.set_ylabel('Género', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_06_generos_por_region.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 7. 03_07_scatter_na_vs_jp.png
sql_7 = """
SELECT title, na_sales, jp_sales
FROM console_games
WHERE na_sales > 0 OR jp_sales > 0
"""
print(f"Ejecutando consulta 7:\n{sql_7}")
df_7 = query_to_dataframe(sql_7)
if not df_7.empty:
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.scatterplot(data=df_7, x='na_sales', y='jp_sales', alpha=0.5, ax=ax)
    ax.set_title('Ventas en Norteamérica vs Ventas en Japón', fontsize=16)
    ax.set_xlabel('Ventas en NA (Millones)', fontsize=12)
    ax.set_ylabel('Ventas en JP (Millones)', fontsize=12)
    
    corr = np.corrcoef(df_7['na_sales'].fillna(0), df_7['jp_sales'].fillna(0))[0, 1]
    ax.text(0.05, 0.95, f'Correlación Pearson: {corr:.2f}', transform=ax.transAxes, fontsize=12, verticalalignment='top')
    
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_07_scatter_na_vs_jp.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 8. 03_08_evolucion_regional.png
sql_8 = """
SELECT 
    decade,
    SUM(na_sales) as NA,
    SUM(jp_sales) as JP,
    SUM(pal_sales) as PAL,
    SUM(other_sales) as Otros
FROM console_games
WHERE decade IS NOT NULL
GROUP BY decade
ORDER BY decade ASC
"""
print(f"Ejecutando consulta 8:\n{sql_8}")
df_8 = query_to_dataframe(sql_8)
if not df_8.empty:
    df_8.set_index('decade', inplace=True)
    fig, ax = plt.subplots(figsize=(12, 6))
    df_8.plot(kind='line', marker='o', ax=ax)
    ax.set_title('Evolución de Ventas Regionales por Década', fontsize=16)
    ax.set_xlabel('Década', fontsize=12)
    ax.set_ylabel('Ventas (Millones)', fontsize=12)
    ax.legend(title='Región')
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_08_evolucion_regional.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 9. 03_09_ventas_medias_por_genero.png
sql_9 = """
SELECT g.genre_name, AVG(cg.total_sales) as mean_sales
FROM console_games cg
JOIN genres g ON cg.genre_id = g.genre_id
GROUP BY g.genre_name
ORDER BY mean_sales DESC
"""
print(f"Ejecutando consulta 9:\n{sql_9}")
df_9 = query_to_dataframe(sql_9)
if not df_9.empty:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df_9, x='genre_name', y='mean_sales', hue='genre_name', legend=False, ax=ax, palette='mako')
    ax.set_title('Ventas Medias por Género', fontsize=16)
    ax.set_xlabel('Género', fontsize=12)
    ax.set_ylabel('Ventas Medias (Millones)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_09_ventas_medias_por_genero.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 10. 03_10_generos_por_decada.png
sql_10 = """
SELECT cg.decade, g.genre_name, COUNT(*) as game_count
FROM console_games cg
JOIN genres g ON cg.genre_id = g.genre_id
WHERE cg.decade IS NOT NULL
GROUP BY cg.decade, g.genre_name
"""
print(f"Ejecutando consulta 10:\n{sql_10}")
df_10 = query_to_dataframe(sql_10)
if not df_10.empty:
    pivot_10 = df_10.pivot(index='genre_name', columns='decade', values='game_count').fillna(0)
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot_10, cmap='crest', annot=True, fmt=".0f", ax=ax)
    ax.set_title('Número de Juegos por Género y Década', fontsize=16)
    ax.set_xlabel('Década', fontsize=12)
    ax.set_ylabel('Género', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_10_generos_por_decada.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 11. 03_11_critic_score_vs_ventas.png
sql_11 = """
SELECT critic_score, total_sales
FROM console_games
WHERE critic_score IS NOT NULL AND total_sales IS NOT NULL
"""
print(f"Ejecutando consulta 11:\n{sql_11}")
df_11 = query_to_dataframe(sql_11)
if not df_11.empty:
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.regplot(data=df_11, x='critic_score', y='total_sales', scatter_kws={'alpha':0.3}, line_kws={'color':'red'}, ax=ax)
    ax.set_title('Puntuación de la Crítica vs Ventas Totales', fontsize=16)
    ax.set_xlabel('Puntuación de la Crítica', fontsize=12)
    ax.set_ylabel('Ventas Totales (Millones)', fontsize=12)
    
    corr = np.corrcoef(df_11['critic_score'], df_11['total_sales'])[0, 1]
    ax.text(0.05, 0.95, f'Correlación Pearson: {corr:.2f}', transform=ax.transAxes, fontsize=12, verticalalignment='top')
    
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_11_critic_score_vs_ventas.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 12. 03_12_critic_score_por_genero.png
sql_12 = """
SELECT g.genre_name, cg.critic_score
FROM console_games cg
JOIN genres g ON cg.genre_id = g.genre_id
WHERE cg.critic_score IS NOT NULL
"""
print(f"Ejecutando consulta 12:\n{sql_12}")
df_12 = query_to_dataframe(sql_12)
if not df_12.empty:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=df_12, x='genre_name', y='critic_score', hue='genre_name', legend=False, ax=ax, palette='Set3')
    ax.set_title('Distribución de Puntuaciones de la Crítica por Género', fontsize=16)
    ax.set_xlabel('Género', fontsize=12)
    ax.set_ylabel('Puntuación de la Crítica', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_12_critic_score_por_genero.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 13. 03_13_top15_publishers.png
sql_13 = """
SELECT publisher, SUM(total_sales) as total_sales
FROM console_games
WHERE publisher IS NOT NULL
GROUP BY publisher
ORDER BY total_sales DESC
LIMIT 15
"""
print(f"Ejecutando consulta 13:\n{sql_13}")
df_13 = query_to_dataframe(sql_13)
if not df_13.empty:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df_13, x='publisher', y='total_sales', hue='publisher', legend=False, ax=ax, palette='cubehelix')
    ax.set_title('Top 15 Editores por Ventas Totales', fontsize=16)
    ax.set_xlabel('Editor', fontsize=12)
    ax.set_ylabel('Ventas Totales (Millones)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_13_top15_publishers.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

# 14. 03_14_big3_portafolio_generos.png
sql_14 = """
SELECT cg.console_manufacturer, g.genre_name, COUNT(*) as game_count
FROM console_games cg
JOIN genres g ON cg.genre_id = g.genre_id
WHERE cg.console_manufacturer IN ('Nintendo', 'Sony', 'Microsoft')
GROUP BY cg.console_manufacturer, g.genre_name
"""
print(f"Ejecutando consulta 14:\n{sql_14}")
df_14 = query_to_dataframe(sql_14)
if not df_14.empty:
    pivot_14 = df_14.pivot(index='genre_name', columns='console_manufacturer', values='game_count').fillna(0)
    pivot_14_pct = pivot_14.div(pivot_14.sum(axis=0), axis=1) * 100
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(pivot_14_pct, cmap='PuBu', annot=True, fmt=".1f", ax=ax)
    ax.set_title('Portafolio de Géneros: Nintendo vs Sony vs Microsoft (%)', fontsize=16)
    ax.set_xlabel('Fabricante', fontsize=12)
    ax.set_ylabel('Género', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGURES_DIR, '03_14_big3_portafolio_generos.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

print("¡Fase 2B completada con éxito!")
