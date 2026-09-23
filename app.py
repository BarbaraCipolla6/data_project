"""
app.py — Dashboard Interactivo Avanzado: MySQL → Pandas → Plotly (Streamlit)
Pipeline: MySQL → SQL queries → Pandas DataFrames → Plotly visualizaciones interactivas de alta fidelidad
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
    page_title="Game Strategy Advisor & BI Studio",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CARGA DE DATOS DESDE MySQL (CON CACHÉ)
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
               sg.playtime_hours, sg.primary_genre, sg.name
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
               g.genre_name AS genre, c.console_abbrev, c.console_full
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
    st.info("💡 Si estás en Streamlit Cloud, asegúrate de configurar los **Secrets** en los ajustes de la app con las credenciales de Aiven MySQL. Si estás en local, verifica que XAMPP esté corriendo.")
    st.stop()

# ============================================================================
# BARRA LATERAL - FILTROS GLOBALES INTERACTIVOS
# ============================================================================
st.sidebar.title("🎮 Filtros interactivos")
st.sidebar.markdown("**Fuente DB:** MySQL Cloud (`Aiven`)")
st.sidebar.markdown("---")

selected_genre = st.sidebar.selectbox(
    "📌 Selecciona un Género Principal:",
    ["Todos"] + all_genres,
    index=all_genres.index("Action") + 1 if "Action" in all_genres else 0
)

min_year = int(df_steam['year'].dropna().min()) if df_steam['year'].min() > 2000 else 2000
max_year = int(df_steam['year'].dropna().max()) if df_steam['year'].max() <= 2025 else 2025
year_range = st.sidebar.slider("🗓️ Rango de Años (Steam):", min_year, max_year, (2010, max_year))

price_category_filter = st.sidebar.multiselect(
    "💵 Categoría de Precio:",
    ['Free', 'Budget', 'Mid', 'Premium', 'AAA'],
    default=['Free', 'Budget', 'Mid', 'Premium', 'AAA']
)

min_reviews_filter = st.sidebar.slider("⭐ Mínimo de Reseñas para Métricas:", 0, 500, 10, step=10)

# Filtrar datasets según selecciones
filtered_steam = df_steam[
    (df_steam['year'] >= year_range[0]) &
    (df_steam['year'] <= year_range[1]) &
    (df_steam['price_category'].isin(price_category_filter)) &
    ((df_steam['positive'] + df_steam['negative']) >= min_reviews_filter)
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
# ENCABEZADO Y KPIS INTERACTIVOS
# ============================================================================
st.title("🎯 Game Strategy Advisor & Market Intelligence")
st.markdown("### Dashboard Interactivo de Inteligencia de Mercado — Pipeline: **MySQL → SQL → Pandas → Plotly**")
st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Juegos Steam", f"{len(filtered_steam_genre):,}")
col2.metric("Mediana Precio", f"${filtered_steam_genre['price'].median():.2f}" if len(filtered_steam_genre) > 0 else "N/A")
col3.metric("Mediana Owners", f"{filtered_steam_genre['owners_midpoint'].median():,.0f}" if len(filtered_steam_genre) > 0 else "N/A")
col4.metric("% Reseñas Positivas", f"{filtered_steam_genre['pct_pos_total'].median():.1f}%" if len(filtered_steam_genre) > 0 else "N/A")
col5.metric("Ventas Consolas (M)", f"${filtered_sales['total_sales'].sum():,.2f}M" if len(filtered_sales) > 0 else "N/A")

st.markdown("---")

# ============================================================================
# PESTAÑAS PRINCIPALES INTERACTIVAS
# ============================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Simulador Estratégico",
    "📊 Mercado Steam & Tendencias",
    "⭐ Expectativa vs Desempeño",
    "🌍 Ventas Globales & Consolas",
    "🔍 Explorador de Datos"
])

# ----------------------------------------------------------------------------
# TAB 1: SIMULADOR ESTRATÉGICO
# ----------------------------------------------------------------------------
with tab1:
    st.subheader("💡 Asesor Estratégico de Producto & Pricing")
    st.write("Simula el lanzamiento de tu juego interactuando con los parámetros clave del mercado:")

    sim_col1, sim_col2, sim_col3 = st.columns(3)

    with sim_col1:
        sim_genre = st.selectbox("Género Objetivo:", all_genres,
                                  index=all_genres.index("RPG") if "RPG" in all_genres else 0)
        sim_tier = st.selectbox("Tier de Presupuesto:",
                                ["Indie Budget ($0-5)", "Indie Mid ($5-15)",
                                 "AA Premium ($15-30)", "AAA ($30+)"], index=1)

    with sim_col2:
        sim_langs = st.slider("Idiomas a Localizar:", 1, 20, 5)
        sim_trailers = st.slider("Trailers de Video Promocionales:", 0, 5, 2)

    with sim_col3:
        sim_platform = st.multiselect("Plataformas Objetivo:",
                                       ["Windows", "Mac", "Linux", "Consolas"],
                                       default=["Windows", "Consolas"])

    # Datos del género seleccionado
    genre_data = df_genres[df_genres['genre'] == sim_genre]
    steam_genre_data = df_steam[df_steam['primary_genre'] == sim_genre]

    avg_owners = genre_data['owners_midpoint'].median() if len(genre_data) > 0 else 10000
    avg_price = steam_genre_data[steam_genre_data['price'] > 0]['price'].median() if len(steam_genre_data) > 0 else 9.99

    loc_multiplier = 1.0 + (sim_langs - 1) * 0.08
    trailer_multiplier = 1.0 + sim_trailers * 0.12
    projected_owners = int(avg_owners * loc_multiplier * trailer_multiplier)
    projected_revenue = projected_owners * avg_price

    st.markdown("#### 📈 Proyección Estimada de Impacto")
    res_col1, res_col2, res_col3, res_col4 = st.columns(4)

    res_col1.metric("Precio Sugerido", f"${avg_price:.2f}")
    res_col2.metric("Alcance Estimado", f"{projected_owners:,}",
                    delta=f"+{(loc_multiplier*trailer_multiplier - 1)*100:.0f}% vs promedio género")
    res_col3.metric("Revenue Bruto Est.", f"${projected_revenue:,.0f}")
    res_col4.metric("Competencia del Género", "Alta" if len(steam_genre_data) > 3000
                    else ("Media" if len(steam_genre_data) > 1000 else "Baja"))

    st.success(f"""
    **📌 Recomendaciones Estratégicas para {sim_genre}:**
    - **Punto dulce de precio:** Fijar el precio alrededor de **\${avg_price:.2f}** maximiza la conversión para este género.
    - **Estrategia de idiomas ({sim_langs} idiomas):** Expandir la localización aumenta tu mercado potencial en un **+{(sim_langs-1)*8:.0f}%**.
    - **Material visual ({sim_trailers} trailers):** La presencia de trailers optimiza la tasa de conversión en la tienda en un **+{sim_trailers*12}%**.
    """)

# ----------------------------------------------------------------------------
# TAB 2: MERCADO STEAM & TENDENCIAS
# ----------------------------------------------------------------------------
with tab2:
    st.subheader("📊 Panorama del Mercado Digital en Steam")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        # Evolución interactiva en área con selector de zoom
        yearly = filtered_steam_genre.groupby('year').size().reset_index(name='juegos')
        fig_year = px.area(
            yearly, x='year', y='juegos',
            title=f"📈 Crecimiento Histórico de Lanzamientos ({selected_genre})",
            labels={'year': 'Año', 'juegos': 'Juegos Publicados'},
            color_discrete_sequence=['#636EFA']
        )
        fig_year.update_xaxes(rangeslider_visible=True)
        fig_year.update_traces(hovertemplate="<b>Año %{x}</b><br>Lanzamientos: %{y:,}<extra></extra>")
        st.plotly_chart(fig_year, use_container_width=True)

    with m_col2:
        # Distribución de Precios con selector de rango
        price_data = filtered_steam_genre[filtered_steam_genre['price'] <= 60]
        fig_price = px.histogram(
            price_data, x='price', nbins=30,
            color='price_category',
            title=f"🏷️ Distribución de Precios por Categoría ({selected_genre})",
            labels={'price': 'Precio ($)', 'price_category': 'Tier'},
            hover_data=['price']
        )
        fig_price.update_layout(barmode='stack')
        st.plotly_chart(fig_price, use_container_width=True)

    st.markdown("---")

    # Matriz de Oportunidad Oferta vs Demanda
    st.subheader("🎯 Matriz de Oportunidad por Género (Oferta vs Demanda)")
    st.caption("Pasa el mouse sobre los puntos para explorar detalles por género. El tamaño representa el % de opiniones positivas.")

    valid_reviews = df_genres[df_genres['pct_pos_total'] >= 0]
    sat_per_genre = valid_reviews.groupby('genre')['pct_pos_total'].mean().reset_index()

    genre_summary = df_genres.groupby('genre').agg(
        oferta=('appid', 'count'),
        demanda=('owners_midpoint', 'median')
    ).reset_index()

    genre_summary = genre_summary.merge(sat_per_genre, on='genre', how='left')
    genre_summary['satisfaccion'] = genre_summary['pct_pos_total'].fillna(50).clip(lower=1)
    genre_summary = genre_summary[(genre_summary['oferta'] > 0) & (genre_summary['demanda'] > 0)]

    fig_bubble = px.scatter(
        genre_summary, x='oferta', y='demanda', size='satisfaccion',
        color='genre', hover_name='genre', text='genre',
        title="Oferta (Juegos Publicados) vs Demanda (Mediana de Owners)",
        labels={'oferta': 'Competencia / Oferta (Total Juegos)', 'demanda': 'Demanda (Mediana Owners)', 'satisfaccion': '% Positivas'},
        log_x=True, log_y=True, size_max=45
    )
    fig_bubble.update_traces(textposition='top center', hovertemplate="<b>%{hovertext}</b><br>Oferta: %{x:,} juegos<br>Demanda: %{y:,.0f} owners<br>% Positivas: %{marker.size:.1f}%<extra></extra>")
    st.plotly_chart(fig_bubble, use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 3: EXPECTATIVA VS DESEMPEÑO
# ----------------------------------------------------------------------------
with tab3:
    st.subheader("⭐ Expectativa vs Desempeño: Metacritic vs Usuarios")
    st.caption("Exploración interactiva de juegos con puntuación de la crítica especializada y reseñas de jugadores.")

    metacritic_df = filtered_steam[
        (filtered_steam['has_metacritic'] == True) &
        (filtered_steam['metacritic_score'] > 0) &
        (filtered_steam['pct_pos_total'] >= 0)
    ]

    if len(metacritic_df) > 0:
        fig_meta = px.scatter(
            metacritic_df,
            x='metacritic_score',
            y='pct_pos_total',
            color='price_category',
            size='owners_midpoint',
            hover_name='name',
            hover_data={'price': ':.2f$', 'owners_midpoint': ':,', 'metacritic_score': True, 'pct_pos_total': True},
            title="Relación Metacritic Score vs Reseñas Positivas de Usuarios",
            labels={
                'metacritic_score': 'Puntuación Crítica (Metacritic 0-100)',
                'pct_pos_total': '% Reseñas Positivas Usuarios',
                'price_category': 'Tier Precio',
                'owners_midpoint': 'Owners'
            },
            size_max=40
        )
        fig_meta.update_traces(hovertemplate="<b>%{hovertext}</b><br>Metacritic: %{x}<br>Usuarios: %{y:.1f}% positive<br>Owners: %{marker.size:,.0f}<extra></extra>")
        st.plotly_chart(fig_meta, use_container_width=True)
    else:
        st.info("No hay juegos con Metacritic en el filtro seleccionado.")

    st.markdown("---")

    # Matriz interactiva de correlación
    st.subheader("🔥 Matriz Interactiva de Correlación entre Métricas del Producto")
    corr_cols = ['price', 'owners_midpoint', 'pct_pos_total', 'peak_ccu', 'playtime_hours', 'num_languages', 'num_screenshots', 'dlc_count', 'achievements']
    valid_corr_df = filtered_steam[corr_cols].dropna()

    if len(valid_corr_df) > 10:
        corr_matrix = valid_corr_df.corr().round(2)
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Matriz de Correlación de Pearson (Nivel Producto & Engagement)"
        )
        st.plotly_chart(fig_corr, use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 4: VENTAS GLOBALES & CONSOLAS
# ----------------------------------------------------------------------------
with tab4:
    st.subheader("🌍 Ventas Globales de Consolas & Distribución Regional")

    v_col1, v_col2 = st.columns(2)

    with v_col1:
        # Donut Chart interactivo de ventas por región
        sales_regions = pd.DataFrame({
            'Región': ['Norteamérica (NA)', 'Europa (PAL)', 'Japón (JP)', 'Otros'],
            'Ventas (M)': [
                filtered_sales['na_sales'].sum(),
                filtered_sales['pal_sales'].sum(),
                filtered_sales['jp_sales'].sum(),
                filtered_sales['other_sales'].sum()
            ]
        })
        fig_donut = px.pie(
            sales_regions, values='Ventas (M)', names='Región', hole=0.45,
            title=f"Cuota de Ventas por Región ({selected_genre})",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_donut.update_traces(textinfo='percent+label', hovertemplate="<b>%{label}</b><br>Ventas: $%{value:.2f}M (%{percent})<extra></extra>")
        st.plotly_chart(fig_donut, use_container_width=True)

    with v_col2:
        # Treemap interactivo de Fabricantes -> Consolas
        valid_console_sales = filtered_sales[filtered_sales['total_sales'] > 0].dropna(subset=['console_manufacturer', 'console_abbrev'])
        if len(valid_console_sales) > 0:
            fig_tree = px.treemap(
                valid_console_sales,
                path=['console_manufacturer', 'console_abbrev'],
                values='total_sales',
                color='console_manufacturer',
                title="Jerarquía de Ventas por Fabricante y Consola (Haz clic para hacer zoom)",
                hover_data=['total_sales']
            )
            fig_tree.update_traces(hovertemplate="<b>%{label}</b><br>Ventas Totales: $%{value:.2f}M<extra></extra>")
            st.plotly_chart(fig_tree, use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 5: EXPLORADOR INTERACTIVO DE JUEGOS
# ----------------------------------------------------------------------------
with tab5:
    st.subheader("🔍 Explorador Avanzado de Juegos (Consulta en Vivo a MySQL)")
    st.write("Filtra, busca y ordena títulos individuales con métricas en tiempo real:")

    search_col1, search_col2 = st.columns([2, 1])

    with search_col1:
        search_query = st.text_input("🔍 Buscar por nombre del juego:", "")

    with search_col2:
        top_n = st.number_input("Número de juegos a mostrar:", min_value=10, max_value=500, value=100, step=10)

    display_df = filtered_steam_genre[[
        'name', 'year', 'primary_genre', 'price', 'price_category',
        'owners_midpoint', 'pct_pos_total', 'peak_ccu', 'playtime_hours'
    ]].copy()

    display_df['playtime_hours'] = display_df['playtime_hours'].round(1)
    display_df.columns = ['Nombre', 'Año', 'Género', 'Precio ($)', 'Tier',
                           'Owners', '% Positivas', 'Peak CCU', 'Horas Jugadas']

    if search_query:
        display_df = display_df[display_df['Nombre'].str.contains(search_query, case=False, na=False)]

    st.dataframe(
        display_df.sort_values(by='Owners', ascending=False).head(top_n),
        use_container_width=True
    )

st.markdown("---")
st.caption("🎮 Pipeline: CSV → Python (limpieza) → MySQL (Aiven) → SQL queries → Pandas → Plotly/Streamlit")
