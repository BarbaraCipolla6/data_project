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

# Estilo personalizado para limpiar márgenes y tipografía
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .stMetric { background-color: rgba(128, 128, 128, 0.08); padding: 10px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Lista de categorías que no son videojuegos puros o contenido sensible/adulto
NON_GAME_CATEGORIES = [
    'Utilities', 'Design & Illustration', 'Animation & Modeling', 'Education',
    'Video Production', 'Game Development', 'Software Training', 'Audio Production',
    '360 Video', 'Documentary', 'Short', 'Tutorial', 'Episodic', 'Photo Editing',
    'Violent', 'Gore', 'Nudity', 'Sexual Content', 'NSFW', 'Hentai', 'Erotica',
    'Accounting', 'Movie', 'Web Publishing'
]

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
    raw_genres = df['genre_name'].dropna().tolist()
    return sorted([g for g in raw_genres if g not in NON_GAME_CATEGORIES])

# Cargar datos
try:
    df_steam = load_steam_base()
    df_genres = load_genres()
    df_sales = load_sales()

    # Filtrar categorías no deseadas globalmente
    df_steam = df_steam[~df_steam['primary_genre'].isin(NON_GAME_CATEGORIES)]
    df_genres = df_genres[~df_genres['genre'].isin(NON_GAME_CATEGORIES)]
    df_sales = df_sales[~df_sales['genre'].isin(NON_GAME_CATEGORIES)]

    all_genres = load_genre_list()
except Exception as e:
    st.info("💡 Si estás en Streamlit Cloud, asegúrate de configurar los **Secrets** en los ajustes de la app con las credenciales de Aiven MySQL. Si estás en local, verifica que XAMPP esté corriendo.")
    st.stop()

# ============================================================================
# BARRA LATERAL - FILTROS GLOBALES INTERACTIVOS
# ============================================================================
st.sidebar.title("🎮 Filtros del Mercado")
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
# ENCABEZADO Y KPIS
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
# PESTAÑAS PRINCIPALES INTERACTIVAS CON DISEÑO DESPEJADO
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
        yearly = filtered_steam_genre.groupby('year').size().reset_index(name='juegos')
        fig_year = px.area(
            yearly, x='year', y='juegos',
            title=f"📈 Crecimiento Histórico de Lanzamientos ({selected_genre})",
            labels={'year': 'Año', 'juegos': 'Juegos Publicados'},
            color_discrete_sequence=['#4C78A8']
        )
        fig_year.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=30))
        fig_year.update_xaxes(rangeslider_visible=True)
        fig_year.update_traces(hovertemplate="<b>Año %{x}</b><br>Lanzamientos: %{y:,}<extra></extra>")
        st.plotly_chart(fig_year, use_container_width=True)

    with m_col2:
        price_data = filtered_steam_genre[filtered_steam_genre['price'] <= 60]
        fig_price = px.histogram(
            price_data, x='price', nbins=24,
            color='price_category',
            title=f"🏷️ Distribución de Precios por Tier ({selected_genre})",
            labels={'price': 'Precio ($)', 'price_category': 'Tier'},
            hover_data=['price']
        )
        fig_price.update_layout(height=380, barmode='stack', margin=dict(l=20, r=20, t=50, b=30))
        st.plotly_chart(fig_price, use_container_width=True)

    st.markdown("---")

    # MATRIZ DE OPORTUNIDAD REORGANIZADA CON MÉTRICAS PRECISAS DE DEMANDA
    st.subheader("🎯 Matriz de Oportunidad Estratégica por Género")
    st.caption("Selecciona la métrica de demanda para evaluar el atractivo relativo de cada género en el mercado.")

    opt_col1, opt_col2 = st.columns([2, 1])

    with opt_col1:
        metric_choice = st.selectbox(
            "📊 Métrica de Demanda a evaluar en el Eje Y:",
            ["Promedio de Jugadores (Owners / Juego)", "Alcance Total del Mercado (Owners Totales)", "Jugadores Simultáneos Promedio (Peak CCU)", "Satisfacción Promedio (% Positivas)"]
        )

    # Filtrar solo géneros principales de videojuegos
    game_genres_df = df_genres[~df_genres['genre'].isin(NON_GAME_CATEGORIES)]
    valid_reviews = game_genres_df[game_genres_df['pct_pos_total'] >= 0]
    sat_per_genre = valid_reviews.groupby('genre')['pct_pos_total'].mean().reset_index()

    genre_summary = game_genres_df.groupby('genre').agg(
        oferta=('appid', 'count'),
        avg_owners=('owners_midpoint', 'mean'),
        total_owners=('owners_midpoint', 'sum'),
        avg_ccu=('peak_ccu', 'mean')
    ).reset_index()

    genre_summary = genre_summary.merge(sat_per_genre, on='genre', how='left')
    genre_summary['satisfaccion'] = genre_summary['pct_pos_total'].fillna(75)
    genre_summary = genre_summary[genre_summary['oferta'] >= 10]

    # Asignación de columna Y según selección
    if metric_choice == "Promedio de Jugadores (Owners / Juego)":
        y_col = 'avg_owners'
        y_label = 'Promedio Owners / Juego'
        hover_fmt = "%{y:,.0f} owners/juego"
    elif metric_choice == "Alcance Total del Mercado (Owners Totales)":
        y_col = 'total_owners'
        y_label = 'Owners Totales Acumulados'
        hover_fmt = "%{y:,.0f} owners totales"
    elif metric_choice == "Jugadores Simultáneos Promedio (Peak CCU)":
        y_col = 'avg_ccu'
        y_label = 'Peak CCU Promedio'
        hover_fmt = "%{y:,.0f} jugadores simultáneos"
    else:
        y_col = 'satisfaccion'
        y_label = '% Reseñas Positivas Promedio'
        hover_fmt = "%{y:.1f}% positivas"

    # Medianas para los cuadrantes
    med_oferta = genre_summary['oferta'].median()
    med_demanda = genre_summary[y_col].median()

    def get_quadrant(row):
        if row[y_col] >= med_demanda and row['oferta'] < med_oferta:
            return '🌟 Nicho de Oportunidad (Baja Oferta, Alta Demanda)'
        elif row[y_col] >= med_demanda and row['oferta'] >= med_oferta:
            return '🔵 Mercado Masivo (Alta Oferta, Alta Demanda)'
        elif row[y_col] < med_demanda and row['oferta'] < med_oferta:
            return '⚪ Mercado Específico (Baja Oferta, Baja Demanda)'
        else:
            return '⚠️ Mercado Saturado (Alta Oferta, Baja Demanda)'

    genre_summary['Cuadrante'] = genre_summary.apply(get_quadrant, axis=1)

    color_map_quads = {
        '🌟 Nicho de Oportunidad (Baja Oferta, Alta Demanda)': '#2CA02C',
        '🔵 Mercado Masivo (Alta Oferta, Alta Demanda)': '#1F77B4',
        '⚪ Mercado Específico (Baja Oferta, Baja Demanda)': '#7F7F7F',
        '⚠️ Mercado Saturado (Alta Oferta, Baja Demanda)': '#D62728'
    }

    fig_bubble = px.scatter(
        genre_summary,
        x='oferta',
        y=y_col,
        color='Cuadrante',
        color_discrete_map=color_map_quads,
        text='genre',
        hover_name='genre',
        title=f"Matriz 2x2: Oferta (Juegos) vs Demanda ({y_label})",
        labels={'oferta': 'Oferta / Competencia (Total Juegos)', y_col: y_label},
        log_x=True,
        log_y=True if y_col != 'satisfaccion' else False
    )

    fig_bubble.update_traces(
        textposition='top center',
        marker=dict(size=14, line=dict(width=1.5, color='white')),
        hovertemplate=f"<b>%{{hovertext}}</b><br>Oferta: %{{x:,}} juegos<br>{y_label}: {hover_fmt}<extra></extra>"
    )

    fig_bubble.add_vline(x=med_oferta, line_dash="dash", line_color="gray", annotation_text="Mediana Oferta")
    fig_bubble.add_hline(y=med_demanda, line_dash="dash", line_color="gray", annotation_text="Mediana Demanda")

    fig_bubble.update_layout(height=520, margin=dict(l=20, r=20, t=50, b=30), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_bubble, use_container_width=True)

    st.markdown("---")

    sub_m1, sub_m2 = st.columns(2)

    with sub_m1:
        # Ranking de Rendimiento Promedio por Juego
        st.subheader("🏆 Promedio de Jugadores por Juego (Atractivo Unitario)")
        rank_df = genre_summary.sort_values(by='avg_owners', ascending=True)

        fig_rank = px.bar(
            rank_df,
            y='genre',
            x='avg_owners',
            color='avg_owners',
            color_continuous_scale='Viridis',
            orientation='h',
            title="Promedio de Owners Estimado por Título Publicado",
            labels={'avg_owners': 'Promedio Owners / Juego', 'genre': 'Género'}
        )
        fig_rank.update_traces(hovertemplate="<b>%{y}</b><br>Promedio: %{x:,.0f} owners/juego<extra></extra>")
        fig_rank.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=30), coloraxis_showscale=False)
        st.plotly_chart(fig_rank, use_container_width=True)

    with sub_m2:
        # Pie Chart de Alcance Total del Mercado por Género
        st.subheader("🥧 Cuota del Mercado Total de Jugadores (Owners Acumulados)")
        fig_pie_genre = px.pie(
            genre_summary,
            values='total_owners',
            names='genre',
            hole=0.45,
            title="Distribución Total de Jugadores Acumulados por Género",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie_genre.update_traces(textinfo='percent+label', hovertemplate="<b>%{label}</b><br>Total Owners: %{value:,.0f} (%{percent})<extra></extra>")
        fig_pie_genre.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=30))
        st.plotly_chart(fig_pie_genre, use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 3: EXPECTATIVA VS DESEMPEÑO
# ----------------------------------------------------------------------------
with tab3:
    st.subheader("⭐ Expectativa vs Desempeño: Análisis Dinámico Crítica vs Usuarios")
    st.caption("Filtra, resalta juegos individuales y compara cómo difiere la opinión de la crítica especializada (Metacritic) frente a los jugadores.")

    # Controles dinámicos superiores
    ctrl1, ctrl2, ctrl3 = st.columns([1.5, 1.5, 2])

    with ctrl1:
        color_mode = st.selectbox(
            "🎨 Modo de Coloración:",
            ["Cuadrante de Opinión", "Categoría de Precio", "Tier de Popularidad"]
        )

    with ctrl2:
        top_sample = st.radio("📊 Muestra de Juegos (por ventas/owners):", [50, 100, 200, "Todos"], index=1, horizontal=True)

    metacritic_df = filtered_steam[
        (filtered_steam['has_metacritic'] == True) &
        (filtered_steam['metacritic_score'] > 0) &
        (filtered_steam['pct_pos_total'] >= 0)
    ].sort_values(by='owners_midpoint', ascending=False)

    with ctrl3:
        all_meta_games = sorted(metacritic_df['name'].dropna().unique().tolist()) if len(metacritic_df) > 0 else []
        highlight_game = st.selectbox("🔎 Resaltar Juego Específico:", ["Ninguno (Ver todos)"] + all_meta_games)

    if top_sample != "Todos":
        metacritic_df = metacritic_df.head(int(top_sample))

    if len(metacritic_df) > 0:
        def get_meta_quadrant(row):
            meta = row['metacritic_score']
            user = row['pct_pos_total']
            if meta >= 75 and user >= 75:
                return '🏆 Éxitos Aclamados (Crítica ≥ 75 & Usuarios ≥ 75%)'
            elif meta < 75 and user >= 75:
                return '💎 Favoritos del Público / Joyas (Crítica < 75 & Usuarios ≥ 75%)'
            elif meta >= 75 and user < 75:
                return '💔 Mimados por la Crítica (Crítica ≥ 75 & Usuarios < 75%)'
            else:
                return '📉 Bajo Rendimiento (Crítica < 75 & Usuarios < 75%)'

        metacritic_df['Cuadrante'] = metacritic_df.apply(get_meta_quadrant, axis=1)

        meta_colors = {
            '🏆 Éxitos Aclamados (Crítica ≥ 75 & Usuarios ≥ 75%)': '#2CA02C',
            '💎 Favoritos del Público / Joyas (Crítica < 75 & Usuarios ≥ 75%)': '#1F77B4',
            '💔 Mimados por la Crítica (Crítica ≥ 75 & Usuarios < 75%)': '#FF7F0E',
            '📉 Bajo Rendimiento (Crítica < 75 & Usuarios < 75%)': '#D62728'
        }

        # Determinación de variable de color
        if color_mode == "Cuadrante de Opinión":
            color_var = 'Cuadrante'
            color_kwargs = {'color_discrete_map': meta_colors}
        elif color_mode == "Categoría de Precio":
            color_var = 'price_category'
            color_kwargs = {}
        else:
            color_var = 'popularity_tier'
            color_kwargs = {}

        fig_meta = px.scatter(
            metacritic_df,
            x='metacritic_score',
            y='pct_pos_total',
            color=color_var,
            hover_name='name',
            custom_data=['price', 'owners_midpoint', 'primary_genre'],
            title=f"Matriz Dinámica: Metacritic (Crítica) vs Reseñas Positivas (Usuarios) — Color: {color_mode}",
            labels={
                'metacritic_score': 'Score Crítica (Metacritic 0-100)',
                'pct_pos_total': '% Reseñas Positivas Usuarios',
                'price_category': 'Tier Precio',
                'popularity_tier': 'Popularidad'
            },
            **color_kwargs
        )

        fig_meta.update_traces(
            marker=dict(size=12, opacity=0.8, line=dict(width=0.8, color='white')),
            hovertemplate="<b>%{hovertext}</b><br>Metacritic: %{x}<br>Usuarios: %{y:.1f}% positivo<br>Precio: $%{customdata[0]:.2f}<br>Owners: %{customdata[1]:,}<br>Género: %{customdata[2]}<extra></extra>"
        )

        # Resaltar juego si el usuario seleccionó uno
        if highlight_game != "Ninguno (Ver todos)":
            target_row = metacritic_df[metacritic_df['name'] == highlight_game]
            if len(target_row) > 0:
                h_x = target_row['metacritic_score'].values[0]
                h_y = target_row['pct_pos_total'].values[0]
                fig_meta.add_trace(
                    go.Scatter(
                        x=[h_x], y=[h_y],
                        mode='markers+text',
                        marker=dict(size=24, color='gold', symbol='star', line=dict(width=2, color='black')),
                        text=[f"  ⭐ {highlight_game}"],
                        textposition="top right",
                        name=f"Resaltado: {highlight_game}"
                    )
                )

        # Líneas divisorias en 75 puntos
        fig_meta.add_vline(x=75, line_dash="dash", line_color="gray", annotation_text="Crítica = 75")
        fig_meta.add_hline(y=75, line_dash="dash", line_color="gray", annotation_text="Usuarios = 75%")

        fig_meta.update_layout(height=520, margin=dict(l=20, r=20, t=50, b=30), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_meta, use_container_width=True)

        st.markdown("---")

        sub_col1, sub_col2 = st.columns(2)

        with sub_col1:
            # Gráfico de Discrepancia Crítica vs Usuarios
            st.subheader("⚡ Brecha de Opinión (Crítica vs Usuarios)")
            gap_df = metacritic_df.copy()
            gap_df['gap'] = gap_df['metacritic_score'] - gap_df['pct_pos_total']
            gap_top = pd.concat([
                gap_df.sort_values(by='gap', ascending=False).head(7),
                gap_df.sort_values(by='gap', ascending=True).head(7)
            ]).drop_duplicates(subset='name')

            gap_top['Tipo'] = np.where(gap_top['gap'] > 0, 'La Crítica lo prefirió más', 'Los Jugadores lo prefirieron más')

            fig_gap = px.bar(
                gap_top.sort_values(by='gap'),
                y='name',
                x='gap',
                color='Tipo',
                orientation='h',
                title="Diferencia de Puntuación (Metacritic - % Usuarios)",
                labels={'gap': 'Diferencia (Puntos)', 'name': 'Juego'},
                color_discrete_map={'La Crítica lo prefirió más': '#E45756', 'Los Jugadores lo prefirieron más': '#4C78A8'}
            )
            fig_gap.update_traces(hovertemplate="<b>%{y}</b><br>Diferencia: %{x:.1f} puntos<extra></extra>")
            fig_gap.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=30))
            st.plotly_chart(fig_gap, use_container_width=True)

        with sub_col2:
            # Boxplot interactivo de Metacritic por Categoría de Precio
            st.subheader("🏷️ Metacritic Score por Tier de Precio")
            fig_box = px.box(
                metacritic_df,
                x='price_category',
                y='metacritic_score',
                color='price_category',
                points="all",
                hover_name='name',
                title="Distribución de Puntuación Crítica por Rango de Precio",
                labels={'price_category': 'Tier de Precio', 'metacritic_score': 'Metacritic Score'}
            )
            fig_box.update_traces(hovertemplate="<b>%{hovertext}</b><br>Score: %{y}<extra></extra>")
            fig_box.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=30))
            st.plotly_chart(fig_box, use_container_width=True)

    else:
        st.info("No hay juegos con Metacritic en el filtro seleccionado.")

    st.markdown("---")

    # Matriz interactiva de correlación despejada
    st.subheader("🔥 Matriz de Correlaciones Nivel Producto")
    corr_cols = ['price', 'owners_midpoint', 'pct_pos_total', 'peak_ccu', 'playtime_hours', 'num_languages', 'num_screenshots', 'dlc_count', 'achievements']
    valid_corr_df = filtered_steam[corr_cols].dropna()

    if len(valid_corr_df) > 10:
        corr_matrix = valid_corr_df.corr().round(2)
        labels_es = ['Precio', 'Owners', '% Positivas', 'Peak CCU', 'Horas Jugadas', 'Idiomas', 'Screenshots', 'DLCs', 'Logros']
        corr_matrix.columns = labels_es
        corr_matrix.index = labels_es

        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Matriz de Correlación de Pearson"
        )
        fig_corr.update_layout(height=450, margin=dict(l=20, r=20, t=50, b=30))
        st.plotly_chart(fig_corr, use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 4: VENTAS GLOBALES & CONSOLAS
# ----------------------------------------------------------------------------
with tab4:
    st.subheader("🌍 Ventas Globales de Consolas & Distribución Regional")

    v_col1, v_col2 = st.columns(2)

    with v_col1:
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
        fig_donut.update_layout(height=450, margin=dict(l=20, r=20, t=50, b=30))
        st.plotly_chart(fig_donut, use_container_width=True)

    with v_col2:
        valid_console_sales = filtered_sales[filtered_sales['total_sales'] > 0].dropna(subset=['console_manufacturer', 'console_abbrev'])
        if len(valid_console_sales) > 0:
            console_tree_df = valid_console_sales.groupby(['console_manufacturer', 'console_abbrev'])['total_sales'].sum().reset_index()

            fig_tree = px.treemap(
                console_tree_df,
                path=['console_manufacturer', 'console_abbrev'],
                values='total_sales',
                color='console_manufacturer',
                title="Jerarquía de Ventas por Fabricante y Consola (Haz clic para hacer zoom)",
                hover_data=['total_sales']
            )
            fig_tree.update_traces(hovertemplate="<b>%{label}</b><br>Ventas Totales: $%{value:.2f}M<extra></extra>")
            fig_tree.update_layout(height=450, margin=dict(l=20, r=20, t=50, b=30))
            st.plotly_chart(fig_tree, use_container_width=True)

# ----------------------------------------------------------------------------
# TAB 5: EXPLORADOR INTERACTIVO DE JUEGOS
# ----------------------------------------------------------------------------
with tab5:
    st.subheader("🔍 Explorador Avanzado de Juegos (Consulta a MySQL)")
    st.write("Filtra, busca y explora la base de datos limpia:")

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
