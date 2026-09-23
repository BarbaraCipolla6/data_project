# 🎮 Análisis del Mercado de Videojuegos

Proyecto de análisis de datos aplicado al mercado de videojuegos, utilizando datos reales para estudiar la relación: **mercado → producto → audiencia → expectativa → desempeño**.

## Pipeline de Datos

```
CSV inicial (2 datasets)
         ↓
  limpieza con Python (NumPy, funciones, parsing)
         ↓
      MySQL (MariaDB via XAMPP)
      9 tablas normalizadas, relaciones M:N
         ↓
   consultas SQL (47 queries documentadas)
   JOINs, GROUP BY, CTEs, Window Functions
         ↓
      Pandas DataFrames
         ↓
   ┌─────────┴─────────┐
   ↓                   ↓
 NumPy             Análisis
 (estadísticas,    (correlaciones,
  normalización)    tendencias)
   └─────────┬─────────┘
             ↓
    Matplotlib/Seaborn (53 gráficos)
    Streamlit + Plotly (dashboard interactivo)
```

## Stack Tecnológico

| Tecnología | Uso |
|---|---|
| **Python 3.14** | Lenguaje principal |
| **NumPy** | Cálculos estadísticos, normalización, correlaciones |
| **Pandas** | Manipulación de DataFrames desde SQL |
| **MySQL/MariaDB** | Base de datos relacional (via XAMPP) |
| **SQL** | 47 queries analíticas con JOINs, CTEs, Window Functions |
| **Matplotlib/Seaborn** | Visualización estática (53 gráficos) |
| **Streamlit + Plotly** | Dashboard interactivo web |

## Estructura del Proyecto

```
videogame-market-analysis/
├── .env                              # Credenciales MySQL
├── app.py                            # Dashboard Streamlit (MySQL → Plotly)
├── requirements.txt
├── README.md
│
├── data/
│   └── raw/                          # CSVs originales
│       ├── games_march2025_cleaned.csv    # Steam (89,618 juegos)
│       └── Video Games Sales...csv        # Consolas (64,016 títulos)
│
├── sql/
│   ├── schema.sql                    # DDL: 9 tablas normalizadas
│   └── consultas_analiticas.sql      # 47 queries documentadas
│
├── notebooks/
│   ├── 01_limpieza_carga_mysql.py    # ETL: CSV → Python → MySQL
│   ├── 02_analisis_mercado_steam.py  # SQL → Pandas → Matplotlib
│   ├── 03_analisis_ventas_global.py  # JOINs SQL → Seaborn
│   ├── 04_producto_audiencia.py      # SQL + NumPy correlaciones
│   ├── 05_expectativa_desempeno.py   # SQL + NumPy normalización
│   └── 06_insights_estrategicos.py   # CTEs + recomendaciones BI
│
├── utils/
│   ├── __init__.py
│   ├── db_connection.py              # Conexión MySQL + query_to_dataframe()
│   ├── cleaning.py                   # Funciones de limpieza Python
│   ├── transformations.py            # Feature engineering
│   ├── statistics.py                 # Funciones estadísticas NumPy
│   └── visualizations.py            # Helpers Matplotlib/Seaborn
│
└── output/
    └── figures/                      # 53 gráficos PNG (300 DPI)
```

## Base de Datos MySQL

### Esquema Normalizado (9 tablas)

| Tabla | Filas | Descripción |
|---|---|---|
| `steam_games` | 89,618 | Juegos de Steam (hechos) |
| `steam_game_genres` | 258,024 | Relación M:N juego↔género |
| `steam_game_tags` | 1,008,987 | Tags con votos |
| `steam_game_publishers` | 90,930 | Relación M:N juego↔publisher |
| `steam_game_developers` | 97,905 | Relación M:N juego↔developer |
| `console_games` | 64,016 | Ventas de consolas (hechos) |
| `genres` | 46 | Catálogo de géneros |
| `publishers` | 49,472 | Catálogo de publishers |
| `consoles` | 81 | Catálogo de consolas |

### Queries SQL Destacadas

- **JOINs**: `SELECT g.genre_name, COUNT(*), AVG(sg.owners_midpoint) FROM steam_game_genres sgg JOIN genres g ON... JOIN steam_games sg ON... GROUP BY...`
- **Window Functions**: `SUM(COUNT(*)) OVER (ORDER BY year) AS acumulado`
- **CTEs**: Publisher growth analysis
- **Subqueries**: Top N dentro de cada grupo

## Cómo Ejecutar

### Requisitos
1. Python 3.10+
2. XAMPP con MySQL/MariaDB corriendo
3. `pip install -r requirements.txt`

### Paso 1: ETL (CSV → MySQL)
```bash
python notebooks/01_limpieza_carga_mysql.py
```

### Paso 2: Análisis (SQL → Pandas → Gráficos)
```bash
python notebooks/02_analisis_mercado_steam.py
python notebooks/03_analisis_ventas_global.py
python notebooks/04_producto_audiencia.py
python notebooks/05_expectativa_desempeno.py
python notebooks/06_insights_estrategicos.py
```

### Paso 3: Dashboard Interactivo
```bash
python -m streamlit run app.py
```
Abrir en `http://localhost:8501`

## Hallazgos Clave

- **Crecimiento exponencial** de Steam desde 2014, 18,000+ juegos lanzados en 2024
- **Precio óptimo**: \$15-\$30 para maximizar revenue (indie premium / AA)
- **NA = 50.7%** de ventas globales de consolas, PAL 29%, JP 10.4%
- **Correlación Critic↔Sales = 0.28** (moderada): la crítica no lo es todo
- **Localización importa**: +5 idiomas → significativamente más owners
- **Material visual**: 2+ trailers correlacionan con mayor adopción
