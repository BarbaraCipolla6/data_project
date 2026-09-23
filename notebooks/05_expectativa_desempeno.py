import sys
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_connection import query_to_dataframe

FIGURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'output', 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)

print("Iniciando Fase 4: Expectativa vs Desempeño...")

# Section 1: Metacritic vs Usuarios (Steam)

# 1. 05_01_metacritic_vs_usuarios.png
print("Generando 05_01_metacritic_vs_usuarios.png...")
df_meta = query_to_dataframe("""
    SELECT name, metacritic_score, pct_pos_total, price_category, owners_midpoint 
    FROM steam_games 
    WHERE has_metacritic = TRUE AND metacritic_score > 0 AND pct_pos_total IS NOT NULL
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_meta, x='metacritic_score', y='pct_pos_total', hue='price_category', alpha=0.6, ax=ax)
m, b = np.polyfit(df_meta['metacritic_score'], df_meta['pct_pos_total'], 1)
ax.plot(df_meta['metacritic_score'], m * df_meta['metacritic_score'] + b, color='red', label='Regresión')
ax.set_title('Metacritic vs Porcentaje de Reseñas Positivas')
ax.set_xlabel('Puntuación Metacritic')
ax.set_ylabel('Reseñas Positivas (%)')
ax.legend(title='Categoría de Precio')
fig.savefig(os.path.join(FIGURES_DIR, '05_01_metacritic_vs_usuarios.png'), dpi=300, bbox_inches='tight')
plt.close(fig)
corr_meta = np.corrcoef(df_meta['metacritic_score'], df_meta['pct_pos_total'])[0, 1]
print(f"Correlación Pearson (Metacritic vs Reseñas Positivas): {corr_meta:.3f}")

# 2. 05_02_metacritic_vs_owners.png
print("Generando 05_02_metacritic_vs_owners.png...")
df_meta_bins = query_to_dataframe("""
    SELECT 
        CASE 
            WHEN metacritic_score < 50 THEN '0-50'
            WHEN metacritic_score < 60 THEN '50-60'
            WHEN metacritic_score < 70 THEN '60-70'
            WHEN metacritic_score < 80 THEN '70-80'
            WHEN metacritic_score < 90 THEN '80-90'
            ELSE '90-100'
        END AS metacritic_bin,
        owners_midpoint
    FROM steam_games
    WHERE has_metacritic = TRUE AND metacritic_score > 0 AND owners_midpoint IS NOT NULL
""")
order = ['0-50', '50-60', '60-70', '70-80', '80-90', '90-100']
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=df_meta_bins, x='metacritic_bin', y='owners_midpoint', order=order, hue='metacritic_bin', legend=False, ax=ax)
ax.set_yscale('log')
ax.set_title('Propietarios según Puntuación de Metacritic')
ax.set_xlabel('Rango de Metacritic')
ax.set_ylabel('Propietarios Estimados (Log)')
fig.savefig(os.path.join(FIGURES_DIR, '05_02_metacritic_vs_owners.png'), dpi=300, bbox_inches='tight')
plt.close(fig)

# 3. 05_03_gap_critica_usuarios.png
print("Generando 05_03_gap_critica_usuarios.png...")
df_gap = query_to_dataframe("""
    SELECT name, (metacritic_score - pct_pos_total) AS gap
    FROM steam_games
    WHERE has_metacritic = TRUE AND metacritic_score > 0 AND pct_pos_total IS NOT NULL AND num_reviews_total > 100
""")
df_gap_top = pd.concat([df_gap.nlargest(15, 'gap'), df_gap.nsmallest(15, 'gap')]).sort_values('gap')
fig, ax = plt.subplots(figsize=(12, 10))
df_gap_top['color'] = np.where(df_gap_top['gap'] > 0, 'green', 'red')
ax.barh(df_gap_top['name'], df_gap_top['gap'], color=df_gap_top['color'])
ax.set_title('Brecha entre Crítica (Metacritic) y Usuarios')
ax.set_xlabel('Brecha (Metacritic - % Positivo)')
fig.savefig(os.path.join(FIGURES_DIR, '05_03_gap_critica_usuarios.png'), dpi=300, bbox_inches='tight')
plt.close(fig)

# Section 2: Critic Score vs Ventas (Console dataset)
print("Generando 05_04_critic_vs_ventas.png...")
df_console = query_to_dataframe("""
    SELECT title, critic_score, total_sales
    FROM console_games
    WHERE critic_score IS NOT NULL AND total_sales IS NOT NULL
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_console, x='critic_score', y='total_sales', alpha=0.5, ax=ax)
df_console_clean = df_console.dropna(subset=['critic_score', 'total_sales'])
m2, b2 = np.polyfit(df_console_clean['critic_score'], df_console_clean['total_sales'], 1)
ax.plot(df_console_clean['critic_score'], m2 * df_console_clean['critic_score'] + b2, color='red', label='Regresión')
ax.set_title('Puntuación de Crítica vs Ventas Totales (Consolas)')
ax.set_xlabel('Puntuación de Crítica')
ax.set_ylabel('Ventas Totales (Millones)')
ax.legend()
fig.savefig(os.path.join(FIGURES_DIR, '05_04_critic_vs_ventas.png'), dpi=300, bbox_inches='tight')
plt.close(fig)
corr_console = np.corrcoef(df_console_clean['critic_score'], df_console_clean['total_sales'])[0, 1]
print(f"Correlación Pearson (Crítica vs Ventas Consolas): {corr_console:.3f}")

print("Generando 05_05_cuadrantes.png...")
median_score = np.median(df_console_clean['critic_score'])
median_sales = np.median(df_console_clean['total_sales'])
fig, ax = plt.subplots(figsize=(10, 8))
sns.scatterplot(data=df_console_clean, x='critic_score', y='total_sales', alpha=0.5, ax=ax)
ax.axvline(median_score, color='red', linestyle='--', label='Mediana Puntuación')
ax.axhline(median_sales, color='blue', linestyle='--', label='Mediana Ventas')
ax.text(median_score + 1, median_sales + 1, 'Alta Crítica, Altas Ventas', color='green')
ax.text(median_score - 15, median_sales + 1, 'Baja Crítica, Altas Ventas', color='orange')
ax.text(median_score + 1, median_sales - 0.5, 'Alta Crítica, Bajas Ventas', color='purple')
ax.text(median_score - 15, median_sales - 0.5, 'Baja Crítica, Bajas Ventas', color='red')
ax.set_yscale('log')
ax.set_title('Cuadrantes de Éxito en Consolas')
ax.set_xlabel('Puntuación de Crítica')
ax.set_ylabel('Ventas Totales (Log)')
ax.legend()
fig.savefig(os.path.join(FIGURES_DIR, '05_05_cuadrantes.png'), dpi=300, bbox_inches='tight')
plt.close(fig)

# Section 3: Sentimiento
print("Generando 05_06_distribucion_sentimiento.png...")
df_sent = query_to_dataframe("""
    SELECT pct_pos_total
    FROM steam_games
    WHERE num_reviews_total > 10 AND pct_pos_total IS NOT NULL
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(data=df_sent, x='pct_pos_total', bins=20, kde=True, ax=ax)
ax.set_title('Distribución de Sentimiento Positivo (Juegos con >10 reseñas)')
ax.set_xlabel('% Reseñas Positivas')
ax.set_ylabel('Cantidad de Juegos')
fig.savefig(os.path.join(FIGURES_DIR, '05_06_distribucion_sentimiento.png'), dpi=300, bbox_inches='tight')
plt.close(fig)

print("Generando 05_07_recientes_vs_totales.png...")
df_recent = query_to_dataframe("""
    SELECT name, pct_pos_recent, pct_pos_total
    FROM steam_games
    WHERE pct_pos_recent IS NOT NULL AND pct_pos_total IS NOT NULL AND num_reviews_total > 50
""")
df_recent['tendencia'] = np.where(df_recent['pct_pos_recent'] > df_recent['pct_pos_total'], 'Mejorando', 'Empeorando')
fig, ax = plt.subplots(figsize=(10, 8))
sns.scatterplot(data=df_recent, x='pct_pos_total', y='pct_pos_recent', hue='tendencia', alpha=0.6, ax=ax)
ax.plot([0, 100], [0, 100], color='gray', linestyle='--', label='y=x (Sin cambio)')
ax.set_title('Sentimiento Reciente vs Total')
ax.set_xlabel('Sentimiento Total (%)')
ax.set_ylabel('Sentimiento Reciente (%)')
ax.legend(title='Tendencia')
fig.savefig(os.path.join(FIGURES_DIR, '05_07_recientes_vs_totales.png'), dpi=300, bbox_inches='tight')
plt.close(fig)
df_recent['diferencia'] = df_recent['pct_pos_recent'] - df_recent['pct_pos_total']
print("Top 10 Mejorando:")
print(df_recent.nlargest(10, 'diferencia')[['name', 'diferencia']])
print("Top 10 Empeorando:")
print(df_recent.nsmallest(10, 'diferencia')[['name', 'diferencia']])

# Section 4: Índice de Éxito Compuesto
print("Calculando Índice de Éxito Compuesto...")
df_success = query_to_dataframe("""
    SELECT name, year, primary_genre, price, price_category, owners_midpoint, review_ratio, pct_pos_total, peak_ccu 
    FROM steam_games 
    WHERE review_ratio IS NOT NULL AND peak_ccu > 0 AND owners_midpoint IS NOT NULL
""")
def min_max_norm(series):
    return (series - np.min(series)) / (np.max(series) - np.min(series))

df_success['norm_owners'] = min_max_norm(df_success['owners_midpoint'])
df_success['norm_ratio'] = min_max_norm(df_success['review_ratio'])
df_success['norm_pct'] = min_max_norm(df_success['pct_pos_total'])
df_success['norm_ccu'] = min_max_norm(df_success['peak_ccu'])
df_success['success_score'] = (
    df_success['norm_owners'] * 0.4 +
    df_success['norm_ratio'] * 0.2 +
    df_success['norm_pct'] * 0.2 +
    df_success['norm_ccu'] * 0.2
)
df_top_success = df_success.nlargest(50, 'success_score')

print("Generando 05_08_top50_exitosos.png...")
fig, ax = plt.subplots(figsize=(12, 10))
df_top30 = df_top_success.head(30).sort_values('success_score')
ax.barh(df_top30['name'], df_top30['success_score'], color='skyblue')
ax.set_title('Top 30 Juegos más Exitosos (Índice Compuesto)')
ax.set_xlabel('Índice de Éxito Compuesto')
fig.savefig(os.path.join(FIGURES_DIR, '05_08_top50_exitosos.png'), dpi=300, bbox_inches='tight')
plt.close(fig)
print("Top 50 Exitosos:")
print(df_top_success[['name', 'success_score', 'owners_midpoint', 'peak_ccu']])

print("Generando 05_09_exito_por_precio.png...")
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=df_success, x='price_category', y='success_score', hue='price_category', legend=False, ax=ax)
ax.set_yscale('log')
ax.set_title('Éxito Compuesto según Categoría de Precio')
ax.set_xlabel('Categoría de Precio')
ax.set_ylabel('Índice de Éxito (Log)')
fig.savefig(os.path.join(FIGURES_DIR, '05_09_exito_por_precio.png'), dpi=300, bbox_inches='tight')
plt.close(fig)

print("Generando 05_10_factores_exito.png...")
factores = ['owners_midpoint', 'review_ratio', 'pct_pos_total', 'peak_ccu', 'price']
correlaciones = []
for f in factores:
    df_f = df_success.dropna(subset=[f, 'success_score'])
    corr = np.corrcoef(df_f[f], df_f['success_score'])[0, 1]
    correlaciones.append((f, corr))

df_corr = pd.DataFrame(correlaciones, columns=['factor', 'correlacion'])
fig, ax = plt.subplots(figsize=(8, 6))
sns.barplot(data=df_corr, x='correlacion', y='factor', hue='factor', legend=False, ax=ax)
ax.set_title('Correlación de Factores con el Índice de Éxito')
ax.set_xlabel('Correlación de Pearson')
ax.set_ylabel('Factor')
fig.savefig(os.path.join(FIGURES_DIR, '05_10_factores_exito.png'), dpi=300, bbox_inches='tight')
plt.close(fig)

print("Fase 4 completada exitosamente.")
