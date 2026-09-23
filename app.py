"""
app.py — Dashboard Interactivo: MySQL → Pandas → Plotly (Streamlit)
Pipeline: MySQL → SQL queries → Pandas DataFrames → Plotly visualizaciones interactivas
"""

import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Agregar path del proyecto para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.db_connection import query_to_dataframe, get_connection

# Configuración de página
st.set_page_config(
    page_title="Game Strategy Advisor & BI",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CARGA DE DATOS DESDE MySQL
# ============================================================================

@st.cache_data(ttl=600)
def load_steam_base():
    """Carga datos base de Steam desde MySQL."""
    return query_to_dataframe("""
        SELECT sg.appid, sg.name, sg.year, sg.month, sg.price, sg.price_category,
               sg.is_free, sg.owners_midpoint, sg.positive, sg.negative,
               sg.review_ratio, sg.pct_pos_total, sg.peak_ccu,
               sg.average_playtime_forever, sg.playtime_hours,
               sg.metacritic_score, sg.has_metacritic,
               sg.num_languages, sg.num_screenshots, sg.num_movies,
               sg.dlc_count, sg.achievements, sg.primary_genre,
               sg.popularity_tier
        FROM steam_games sg
    """)

@st.cache_data(ttl=600)
def load_genres():
    """Géneros de Steam con datos del juego (tabla exploded via SQL JOIN)."""
    return query_to_dataframe("""
        SELECT sgg.appid, g.genre_name AS genre,
               sg.year, sg.price, sg.price_category, sg.is_free,
               sg.owners_midpoint, sg.pct_pos_total, sg.peak_ccu,
               sg.playtime_hours, sg.primary_genre
        FROM steam_game_genres sgg
        JOIN genres g ON g.genre_id = sgg.genre_id
        JOIN steam_games sg ON sg.appid = sgg.appid
    """)

@st.cache_data(ttl=600)
def load_sales():
    """Datos de ventas de consolas desde MySQL."""
    return query_to_dataframe("""
        SELECT cg.title, cg.total_sales, cg.na_sales, cg.jp_sales,
               cg.pal_sales, cg.other_sales, cg.year, cg.decade,
               cg.critic_score, cg.dominant_region,
               cg.console_generation, cg.console_manufacturer,
               g.genre_name AS genre, c.console_abbrev
        FROM console_games cg
        LEFT JOIN genres g ON g.genre_id = cg.genre_id
        LEFT JOIN consoles c ON c.console_id = cg.console_id
    """)

@st.cache_data(ttl=600)
def load_genre_list():
    """Lista de géneros disponibles desde MySQL."""
    df = query_to_dataframe("SELECT DISTINCT genre_name FROM genres ORDER BY genre_name")
    return sorted(df['genre_name'].dropna().tolist())

# Cargar datos
try:
    df_steam = load_steam_base()
    df_genres = load_genres()
    df_sales = load_sales()
    all_genres = load_genre_list()
except Exception as e:
    st.error(f"❌ Error al conectar con MySQL: {e}")
    st.info("Asegúrate de que XAMPP MySQL esté corriendo y ejecutá `01_limpieza_carga_mysql.py` primero.")
    st.stop()

# ============================================================================
# BARRA LATERAL - FILTROS GLOBALES
# ============================================================================
st.sidebar.title("🎮 Filtros del Mercado")
st.sidebar.markdown("**Fuente: MySQL** `videogame_market_analysis`")
st.sidebar.markdown("---")

selected_genre = st.sidebar.selectbox(
    "Selecciona un Género Principal:",
    ["Todos"] + all_genres,
    index=all_genres.index("Action") + 1 if "Action" in all_genres else 0
)

min_year = int(df_steam['year'].dropna().min()) if df_steam['year'].min() > 2000 else 2000
max_year = int(df_steam['year'].dropna().max()) if df_steam['year'].max() <= 2025 else 2025
year_range = st.sidebar.slider("Rango de Años (Steam):", min_year, max_year, (2015, max_year))

price_category_filter = st.sidebar.multiselect(
    "Categoría de Precio:",
    ['Free', 'Budget', 'Mid', 'Premium', 'AAA'],
    default=['Free', 'Budget', 'Mid', 'Premium', 'AAA']
)

# Filtrar datasets según selecciones
filtered_steam = df_steam[
    (df_steam['year'] >= year_range[0]) &
    (df_steam['year'] <= year_range[1]) &
    (df_steam['price_category'].isin(price_category_filter))
]

if selected_genre != "Todos":
    filtered_genres = df_genres[
        (df_genres['genre'] == selected_genre) &
        (df_genres['year'] >= year_range[0]) &
        (df_genres['year'] <= year_range[1])
    ]
    filtered_steam_genre = filtered_steam[filtered_steam['primary_genre'] == selected_genre]
    filtered_sales = df_sales[df_sales['genre'] == selected_genre]
else:
    filtered_genres = df_genres[
        (df_genres['year'] >= year_range[0]) &
        (df_genres['year'] <= year_range[1])
    ]
    filtered_steam_genre = filtered_steam
    filtered_sales = df_sales

# ============================================================================
# ENCABEZADO Y KPIS
# ============================================================================
st.title("🎯 Game Strategy Advisor & Market Intelligence")
st.markdown("### Plataforma de Análisis de Datos — Pipeline: MySQL → Pandas → Plotly")
st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Juegos Steam", f"{len(filtered_steam_genre):,}")
col2.metric("Mediana Precio", f"${filtered_steam_genre['price'].median():.2f}" if len(filtered_steam_genre) > 0 else "N/A")
col3.metric("Mediana Owners", f"{filtered_steam_genre['owners_midpoint'].median():,.0f}" if len(filtered_steam_genre) > 0 else "N/A")
col4.metric("% Positivas", f"{filtered_steam_genre['pct_pos_total'].median():.1f}%" if len(filtered_steam_genre) > 0 else "N/A")
col5.metric("Ventas Consolas (M)", f"{filtered_sales['total_sales'].sum():,.2f}M" if len(filtered_sales) > 0 else "N/A")

st.markdown("---")

# ============================================================================
# PESTAÑAS PRINCIPALES
# ============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Simulador Estratégico",
    "📊 Mercado Steam",
    "🌍 Ventas Regionales",
    "🔍 Explorador de Juegos"
])

# ---------- TAB 1: SIMULADOR ----------
with tab1:
    st.subheader("💡 Asesor Estratégico de Producto & Pricing")
    st.write("Simula el lanzamiento de tu videojuego — datos desde **MySQL**:")

    sim_col1, sim_col2, sim_col3 = st.columns(3)

    with sim_col1:
        sim_genre = st.selectbox("Género Objetivo:", all_genres,
                                  index=all_genres.index("RPG") if "RPG" in all_genres else 0)
        sim_tier = st.selectbox("Tier de Presupuesto:",
                                ["Indie Budget ($0-5)", "Indie Mid ($5-15)",
                                 "AA Premium ($15-30)", "AAA ($30+)"], index=1)

    with sim_col2:
        sim_langs = st.slider("Idiomas a Localizar:", 1, 20, 5)
        sim_trailers = st.slider("Trailers de Video:", 0, 5, 2)

    with sim_col3:
        sim_platform = st.multiselect("Plataformas:",
                                       ["Windows", "Mac", "Linux", "Consolas"],
                                       default=["Windows", "Consolas"])

    # Datos del género seleccionado (desde MySQL ya cargado)
    genre_data = df_genres[df_genres['genre'] == sim_genre]
    steam_genre_data = df_steam[df_steam['primary_genre'] == sim_genre]

    avg_owners = genre_data['owners_midpoint'].median() if len(genre_data) > 0 else 10000
    avg_price = steam_genre_data[steam_genre_data['price'] > 0]['price'].median() if len(steam_genre_data) > 0 else 9.99

    loc_multiplier = 1.0 + (sim_langs - 1) * 0.08
    trailer_multiplier = 1.0 + sim_trailers * 0.12
    projected_owners = int(avg_owners * loc_multiplier * trailer_multiplier)

    st.markdown("#### 📈 Resultados Estimados")
    res_col1, res_col2, res_col3, res_col4 = st.columns(4)

    res_col1.metric("Precio Sugerido", f"${avg_price:.2f}")
    res_col2.metric("Alcance Estimado", f"{projected_owners:,}",
                    delta=f"+{(loc_multiplier*trailer_multiplier - 1)*100:.0f}% vs promedio")
    res_col3.metric("Competencia", "Alta" if len(steam_genre_data) > 3000
                    else ("Media" if len(steam_genre_data) > 1000 else "Baja"))
    res_col4.metric("Mes Sugerido", "Marzo / Sept",
                    help="Meses fuera de picos de ofertas")

    st.success(f"""
    **📌 Recomendaciones para un juego {sim_genre}:**
    - **Precio óptimo:** ~**\${avg_price:.2f}** (mediana del género)
    - **Idiomas:** {sim_langs} idiomas → +{(sim_langs-1)*8}% mercado accesible
    - **Trailers:** {sim_trailers} trailers → +{sim_trailers*12}% tasa de adquisición
    - **Pipeline:** Datos extraídos de MySQL (`steam_games` + `genres` + JOINs)
    """)

# ---------- TAB 2: MERCADO STEAM ----------
with tab2:
    st.subheader("📊 Panorama del Mercado Digital en Steam")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        yearly = filtered_steam_genre.groupby('year').size().reset_index(name='juegos')
        fig_year = px.bar(yearly, x='year', y='juegos',
                          title=f"Lanzamientos Anuales ({selected_genre})",
                          labels={'year': 'Año', 'juegos': 'Juegos'},
                          color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig_year, use_container_width=True)

    with m_col2:
        price_data = filtered_steam_genre[filtered_steam_genre['price'] <= 60]
        fig_price = px.histogram(price_data, x='price', nbins=30,
                                  title=f"Distribución de Precios ({selected_genre})",
                                  labels={'price': 'Precio ($)'},
                                  color_discrete_sequence=['#EF553B'])
        st.plotly_chart(fig_price, use_container_width=True)

    st.markdown("---")

    # Matriz de Oportunidad
    st.subheader("🎯 Matriz Oferta vs Demanda (SQL GROUP BY + Pandas)")
    
    # Filtrar solo registros con reviews válidos (pct_pos_total >= 0) para el cálculo de satisfacción
    valid_reviews = df_genres[df_genres['pct_pos_total'] >= 0]
    sat_per_genre = valid_reviews.groupby('genre')['pct_pos_total'].mean().reset_index()
    
    genre_summary = df_genres.groupby('genre').agg(
        oferta=('appid', 'count'),
        demanda=('owners_midpoint', 'median')
    ).reset_index()
    
    genre_summary = genre_summary.merge(sat_per_genre, on='genre', how='left')
    genre_summary['satisfaccion'] = genre_summary['pct_pos_total'].fillna(50).clip(lower=1)
    
    # Filtrar valores positivos para log scale
    genre_summary = genre_summary[(genre_summary['oferta'] > 0) & (genre_summary['demanda'] > 0)]

    fig_bubble = px.scatter(
        genre_summary, x='oferta', y='demanda', size='satisfaccion',
        color='genre', hover_name='genre', text='genre',
        title="Oferta vs Demanda por Género (Tamaño = % Reseñas Positivas)",
        labels={'oferta': 'Oferta (Total Juegos)', 'demanda': 'Demanda (Mediana Owners)', 'satisfaccion': '% Positivas'},
        log_x=True, log_y=True
    )
    fig_bubble.update_traces(textposition='top center')
    st.plotly_chart(fig_bubble, use_container_width=True)

# ---------- TAB 3: VENTAS REGIONALES ----------
with tab3:
    st.subheader("🌍 Análisis Regional (Consolas)")

    reg_col1, reg_col2 = st.columns(2)

    with reg_col1:
        sales_regions = pd.DataFrame({
            'Región': ['Norteamérica (NA)', 'Europa (PAL)', 'Japón (JP)', 'Otros'],
            'Ventas (M)': [
                filtered_sales['na_sales'].sum(),
                filtered_sales['pal_sales'].sum(),
                filtered_sales['jp_sales'].sum(),
                filtered_sales['other_sales'].sum()
            ]
        })
        fig_donut = px.pie(sales_regions, values='Ventas (M)', names='Región',
                           hole=0.4, title=f"Ventas por Región ({selected_genre})",
                           color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_donut, use_container_width=True)

    with reg_col2:
        gen_sales = filtered_sales.groupby('console_generation')['total_sales'].sum().reset_index()
        gen_sales = gen_sales.dropna()
        fig_gen = px.bar(gen_sales, x='console_generation', y='total_sales',
                         title="Ventas por Generación de Consola",
                         labels={'console_generation': 'Generación', 'total_sales': 'Ventas (M)'},
                         color='console_generation')
        st.plotly_chart(fig_gen, use_container_width=True)

# ---------- TAB 4: EXPLORADOR ----------
with tab4:
    st.subheader("🔍 Explorador Interactivo de Juegos (desde MySQL)")
    st.write("Busca en la base de datos MySQL `videogame_market_analysis`:")

    search_query = st.text_input("Buscar por nombre:", "")

    display_df = filtered_steam_genre[[
        'name', 'year', 'primary_genre', 'price', 'price_category',
        'owners_midpoint', 'pct_pos_total', 'peak_ccu', 'average_playtime_forever'
    ]].copy()
    display_df['average_playtime_forever'] = (display_df['average_playtime_forever'] / 60).round(1)
    display_df.columns = ['Nombre', 'Año', 'Género', 'Precio ($)', 'Tier',
                           'Owners', '% Positivas', 'Peak CCU', 'Horas Jugadas']

    if search_query:
        display_df = display_df[display_df['Nombre'].str.contains(search_query, case=False, na=False)]

    st.dataframe(
        display_df.sort_values(by='Owners', ascending=False).head(200),
        use_container_width=True
    )

st.markdown("---")
st.caption("🎮 Pipeline: CSV → Python (limpieza) → MySQL → SQL queries → Pandas → Plotly/Streamlit")
