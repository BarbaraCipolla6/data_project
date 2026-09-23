import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_connection import query_to_dataframe

matplotlib.use('Agg')

FIGURES_DIR = r"C:\Users\barba\.gemini\antigravity\scratch\videogame-market-analysis\output\figures"
os.makedirs(FIGURES_DIR, exist_ok=True)

print("Iniciando Fase 3: Producto y Audiencia")

# Section 1: Géneros y Tags (SQL JOINs)
# 1. 04_01_top20_generos_cantidad.png
print("Generando Top 20 géneros por cantidad de juegos...")
df_genres_count = query_to_dataframe("""
    SELECT g.genre_name, COUNT(*) AS juegos
    FROM steam_game_genres sgg
    JOIN genres g ON g.genre_id = sgg.genre_id
    GROUP BY g.genre_name
    ORDER BY juegos DESC
    LIMIT 20
""")
fig, ax = plt.subplots(figsize=(12, 8))
sns.barplot(data=df_genres_count, x='juegos', y='genre_name', hue='genre_name', legend=False, palette='viridis', ax=ax)
ax.set_title("Top 20 Géneros por Cantidad de Juegos")
ax.set_xlabel("Cantidad de Juegos")
ax.set_ylabel("Género")
fig.savefig(os.path.join(FIGURES_DIR, "04_01_top20_generos_cantidad.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 2. 04_02_top20_generos_owners.png
print("Generando Top 20 géneros por cantidad de propietarios...")
df_genres_owners = query_to_dataframe("""
    SELECT g.genre_name, SUM(sg.owners_midpoint) AS total_owners
    FROM steam_game_genres sgg
    JOIN genres g ON g.genre_id = sgg.genre_id
    JOIN steam_games sg ON sg.appid = sgg.appid
    GROUP BY g.genre_name
    ORDER BY total_owners DESC
    LIMIT 20
""")
fig, ax = plt.subplots(figsize=(12, 8))
sns.barplot(data=df_genres_owners, x='total_owners', y='genre_name', hue='genre_name', legend=False, palette='mako', ax=ax)
ax.set_title("Top 20 Géneros por Propietarios Estimados")
ax.set_xlabel("Propietarios (Suma de Puntos Medios)")
ax.set_ylabel("Género")
fig.savefig(os.path.join(FIGURES_DIR, "04_02_top20_generos_owners.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 3. 04_03_generos_por_decada.png
print("Generando evolución de géneros por década...")
df_genres_decade = query_to_dataframe("""
    SELECT 
        CASE 
            WHEN year < 2000 THEN 'Pre-2000'
            WHEN year >= 2000 AND year < 2010 THEN '2000s'
            WHEN year >= 2010 AND year < 2020 THEN '2010s'
            WHEN year >= 2020 THEN '2020s'
        END AS decada,
        g.genre_name,
        COUNT(*) AS juegos
    FROM steam_game_genres sgg
    JOIN genres g ON g.genre_id = sgg.genre_id
    JOIN steam_games sg ON sg.appid = sgg.appid
    WHERE year > 1980
    GROUP BY decada, g.genre_name
""")
# Filtrar top 5 géneros generales para que el gráfico sea legible
top_genres_dec = df_genres_decade.groupby('genre_name')['juegos'].sum().nlargest(5).index
df_g_dec = df_genres_decade[df_genres_decade['genre_name'].isin(top_genres_dec)]
fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(data=df_g_dec, x='decada', y='juegos', hue='genre_name', marker='o', ax=ax)
ax.set_title("Evolución de los Top 5 Géneros por Década")
ax.set_xlabel("Década")
ax.set_ylabel("Cantidad de Juegos")
fig.savefig(os.path.join(FIGURES_DIR, "04_03_generos_por_decada.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 4. 04_04_top30_tags.png
print("Generando Top 30 tags...")
df_tags = query_to_dataframe("""
    SELECT tag_name, SUM(tag_votes) AS total_votes
    FROM steam_game_tags
    GROUP BY tag_name
    ORDER BY total_votes DESC
    LIMIT 30
""")
fig, ax = plt.subplots(figsize=(12, 10))
sns.barplot(data=df_tags, x='total_votes', y='tag_name', hue='tag_name', legend=False, palette='magma', ax=ax)
ax.set_title("Top 30 Tags por Votos Totales")
ax.set_xlabel("Votos Totales")
ax.set_ylabel("Tag")
fig.savefig(os.path.join(FIGURES_DIR, "04_04_top30_tags.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# Section 2: Producto vs Engagement
# 5. 04_05_achievements_vs_playtime.png
print("Generando Achievements vs Playtime...")
df_achiev = query_to_dataframe("""
    SELECT achievements, average_playtime_forever
    FROM steam_games
    WHERE achievements > 0 AND achievements < 500
    AND average_playtime_forever > 0 AND average_playtime_forever < 10000
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_achiev, x='achievements', y='average_playtime_forever', alpha=0.3, ax=ax)
ax.set_title("Logros vs Tiempo de Juego Promedio")
ax.set_xlabel("Cantidad de Logros")
ax.set_ylabel("Tiempo de Juego (Minutos)")
fig.savefig(os.path.join(FIGURES_DIR, "04_05_achievements_vs_playtime.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 6. 04_06_dlc_vs_owners.png
print("Generando DLC vs Owners...")
df_dlc = query_to_dataframe("""
    SELECT dlc_count, owners_midpoint
    FROM steam_games
    WHERE dlc_count > 0 AND dlc_count < 100
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_dlc, x='dlc_count', y='owners_midpoint', alpha=0.3, ax=ax)
ax.set_yscale('log')
ax.set_title("Cantidad de DLCs vs Propietarios (Escala Log)")
ax.set_xlabel("Cantidad de DLCs")
ax.set_ylabel("Propietarios Estimados")
fig.savefig(os.path.join(FIGURES_DIR, "04_06_dlc_vs_owners.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 7. 04_07_idiomas_vs_owners.png
print("Generando Idiomas vs Owners...")
df_lang = query_to_dataframe("""
    SELECT 
        CASE 
            WHEN num_languages = 1 THEN '1 Idioma'
            WHEN num_languages BETWEEN 2 AND 5 THEN '2-5 Idiomas'
            WHEN num_languages BETWEEN 6 AND 10 THEN '6-10 Idiomas'
            ELSE 'Más de 10'
        END AS lang_bins,
        owners_midpoint
    FROM steam_games
    WHERE owners_midpoint > 0
""")
order = ['1 Idioma', '2-5 Idiomas', '6-10 Idiomas', 'Más de 10']
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=df_lang, x='lang_bins', y='owners_midpoint', hue='lang_bins', legend=False, order=order, ax=ax)
ax.set_yscale('log')
ax.set_title("Cantidad de Idiomas vs Propietarios")
ax.set_xlabel("Grupos de Idiomas")
ax.set_ylabel("Propietarios Estimados (Escala Log)")
fig.savefig(os.path.join(FIGURES_DIR, "04_07_idiomas_vs_owners.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 8. 04_08_marketing_vs_owners.png
print("Generando Marketing vs Owners...")
df_screenshots = query_to_dataframe("""
    SELECT num_screenshots, owners_midpoint
    FROM steam_games
    WHERE num_screenshots > 0 AND num_screenshots < 50
    AND owners_midpoint > 0
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_screenshots, x='num_screenshots', y='owners_midpoint', alpha=0.3, ax=ax)
ax.set_yscale('log')
ax.set_title("Cantidad de Capturas de Pantalla vs Propietarios")
ax.set_xlabel("Capturas de Pantalla")
ax.set_ylabel("Propietarios Estimados (Escala Log)")
fig.savefig(os.path.join(FIGURES_DIR, "04_08_marketing_vs_owners.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# Section 3: Audiencia
# 9. 04_09_distribucion_playtime.png
print("Generando Distribución de Playtime...")
df_playtime = query_to_dataframe("""
    SELECT average_playtime_forever
    FROM steam_games
    WHERE average_playtime_forever > 0 AND average_playtime_forever < 2000
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(data=df_playtime, x='average_playtime_forever', bins=50, kde=True, ax=ax)
ax.set_title("Distribución del Tiempo de Juego Promedio")
ax.set_xlabel("Tiempo de Juego (Minutos)")
ax.set_ylabel("Frecuencia")
fig.savefig(os.path.join(FIGURES_DIR, "04_09_distribucion_playtime.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 10. 04_10_playtime_por_genero.png
print("Generando Playtime por Género (Top 12)...")
df_pt_genre = query_to_dataframe("""
    SELECT g.genre_name, sg.average_playtime_forever
    FROM steam_game_genres sgg
    JOIN genres g ON g.genre_id = sgg.genre_id
    JOIN steam_games sg ON sg.appid = sgg.appid
    WHERE sg.average_playtime_forever > 0 AND sg.average_playtime_forever < 5000
    AND g.genre_name IN (
        SELECT genre_name FROM (
            SELECT g2.genre_name, COUNT(*) as cnt
            FROM steam_game_genres sgg2
            JOIN genres g2 ON g2.genre_id = sgg2.genre_id
            GROUP BY g2.genre_name
            ORDER BY cnt DESC
            LIMIT 12
        ) t
    )
""")
fig, ax = plt.subplots(figsize=(14, 8))
sns.boxplot(data=df_pt_genre, x='average_playtime_forever', y='genre_name', hue='genre_name', legend=False, ax=ax)
ax.set_title("Tiempo de Juego Promedio por Género (Top 12)")
ax.set_xlabel("Tiempo de Juego (Minutos)")
ax.set_ylabel("Género")
fig.savefig(os.path.join(FIGURES_DIR, "04_10_playtime_por_genero.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 11. 04_11_precio_vs_playtime.png
print("Generando Precio vs Playtime...")
df_price_pt = query_to_dataframe("""
    SELECT sg.price, sg.average_playtime_forever, g.genre_name
    FROM steam_games sg
    JOIN steam_game_genres sgg ON sg.appid = sgg.appid
    JOIN genres g ON sgg.genre_id = g.genre_id
    WHERE sg.price > 0 AND sg.price < 100
    AND sg.average_playtime_forever > 0 AND sg.average_playtime_forever < 5000
    AND g.genre_name IN ('Action', 'Adventure', 'RPG', 'Strategy')
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_price_pt, x='price', y='average_playtime_forever', hue='genre_name', alpha=0.5, ax=ax)
ax.set_title("Precio vs Tiempo de Juego Promedio (Géneros Seleccionados)")
ax.set_xlabel("Precio ($)")
ax.set_ylabel("Tiempo de Juego (Minutos)")
fig.savefig(os.path.join(FIGURES_DIR, "04_11_precio_vs_playtime.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 12. 04_12_peak_ccu_vs_owners.png
print("Generando Peak CCU vs Owners...")
df_ccu = query_to_dataframe("""
    SELECT peak_ccu, owners_midpoint
    FROM steam_games
    WHERE peak_ccu > 0 AND owners_midpoint > 0
""")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=df_ccu, x='peak_ccu', y='owners_midpoint', alpha=0.4, ax=ax)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_title("Pico de Jugadores Simultáneos vs Propietarios Estimados")
ax.set_xlabel("Pico de Jugadores Simultáneos (Log)")
ax.set_ylabel("Propietarios Estimados (Log)")
fig.savefig(os.path.join(FIGURES_DIR, "04_12_peak_ccu_vs_owners.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# Section 4: Correlaciones
# 13. 04_13_matriz_correlaciones.png
print("Calculando Matriz de Correlaciones...")
df_corr_data = query_to_dataframe("""
    SELECT price, owners_midpoint, positive, negative, review_ratio, pct_pos_total,
           num_reviews_total, average_playtime_forever, peak_ccu, metacritic_score,
           num_languages, num_screenshots, dlc_count, achievements
    FROM steam_games
""")
# Eliminar nulos para la correlación
df_corr_data = df_corr_data.dropna()

# Calcular matriz de correlación con numpy (usaremos pandas internamente que usa numpy)
corr_matrix = df_corr_data.corr(method='pearson')

fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', ax=ax, vmin=-1, vmax=1)
ax.set_title("Matriz de Correlaciones de Atributos de Juegos")
fig.savefig(os.path.join(FIGURES_DIR, "04_13_matriz_correlaciones.png"), dpi=300, bbox_inches='tight')
plt.close(fig)

# 14. Print top 10 strongest correlations
print("\n--- Top 10 Correlaciones Más Fuertes (Excluyendo Auto-correlaciones) ---")
# Obtener pares
corr_pairs = corr_matrix.unstack().reset_index()
corr_pairs.columns = ['Var1', 'Var2', 'Correlacion']
# Filtrar donde Var1 != Var2
corr_pairs = corr_pairs[corr_pairs['Var1'] != corr_pairs['Var2']]
# Valor absoluto
corr_pairs['Abs_Corr'] = corr_pairs['Correlacion'].abs()
# Ordenar y tomar la mitad (ya que la matriz es simétrica)
top_corrs = corr_pairs.sort_values(by='Abs_Corr', ascending=False).drop_duplicates(subset=['Abs_Corr']).head(10)

for idx, row in top_corrs.iterrows():
    print(f"{row['Var1']} <-> {row['Var2']}: {row['Correlacion']:.4f}")

print("Fase 3 completada con éxito.")
