-- ============================================================================
-- consultas_analiticas.sql
-- Queries SQL documentadas para el análisis del mercado de videojuegos
-- Estas queries alimentan los scripts de análisis (Pandas → NumPy → Matplotlib)
-- ============================================================================

USE videogame_market_analysis;

-- ============================================================================
-- FASE 2A: ANÁLISIS DEL MERCADO DIGITAL (STEAM)
-- ============================================================================

-- Q01: Evolución de lanzamientos por año
SELECT year, COUNT(*) AS juegos
FROM steam_games
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;

-- Q02: Crecimiento acumulado del catálogo
SELECT year,
       COUNT(*) AS juegos_anuales,
       SUM(COUNT(*)) OVER (ORDER BY year) AS acumulado
FROM steam_games
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year;

-- Q03: Estacionalidad de lanzamientos por mes
SELECT month, COUNT(*) AS juegos
FROM steam_games
WHERE month IS NOT NULL
GROUP BY month
ORDER BY month;

-- Q04: Distribución de precios (estadísticas descriptivas)
SELECT
    COUNT(*) AS total_juegos,
    AVG(price) AS precio_medio,
    MIN(price) AS precio_min,
    MAX(price) AS precio_max,
    SUM(CASE WHEN is_free = TRUE THEN 1 ELSE 0 END) AS juegos_gratuitos
FROM steam_games;

-- Q05: Distribución por categoría de precio
SELECT price_category,
       COUNT(*) AS cantidad,
       AVG(price) AS precio_medio,
       AVG(owners_midpoint) AS owners_medio
FROM steam_games
GROUP BY price_category
ORDER BY AVG(price);

-- Q06: Evolución del precio medio por año
SELECT year,
       AVG(price) AS precio_medio,
       AVG(CASE WHEN price > 0 THEN price END) AS precio_medio_pagos
FROM steam_games
WHERE year >= 2000
GROUP BY year
ORDER BY year;

-- Q07: Proporción free vs paid por año
SELECT year,
       SUM(CASE WHEN is_free = TRUE THEN 1 ELSE 0 END) AS gratuitos,
       SUM(CASE WHEN is_free = FALSE THEN 1 ELSE 0 END) AS de_pago,
       ROUND(100.0 * SUM(CASE WHEN is_free = TRUE THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_free
FROM steam_games
WHERE year >= 2000
GROUP BY year
ORDER BY year;

-- Q08: Precio medio por género (top 15)
SELECT g.genre_name,
       COUNT(*) AS juegos,
       AVG(sg.price) AS precio_medio,
       AVG(CASE WHEN sg.price > 0 THEN sg.price END) AS precio_medio_pagos
FROM steam_game_genres sgg
JOIN steam_games sg ON sg.appid = sgg.appid
JOIN genres g ON g.genre_id = sgg.genre_id
GROUP BY g.genre_name
ORDER BY juegos DESC
LIMIT 15;

-- Q09: Distribución de plataformas (Windows/Mac/Linux)
SELECT
    SUM(CASE WHEN windows = TRUE THEN 1 ELSE 0 END) AS windows_count,
    SUM(CASE WHEN mac = TRUE THEN 1 ELSE 0 END) AS mac_count,
    SUM(CASE WHEN linux = TRUE THEN 1 ELSE 0 END) AS linux_count,
    COUNT(*) AS total
FROM steam_games;

-- Q10: Evolución del soporte multiplataforma por año
SELECT year,
       COUNT(*) AS total,
       ROUND(100.0 * SUM(CASE WHEN windows THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_windows,
       ROUND(100.0 * SUM(CASE WHEN mac THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_mac,
       ROUND(100.0 * SUM(CASE WHEN linux THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_linux
FROM steam_games
WHERE year >= 2000
GROUP BY year
ORDER BY year;

-- Q11: Top 20 publishers por cantidad de juegos
SELECT p.publisher_name, COUNT(*) AS juegos
FROM steam_game_publishers sgp
JOIN publishers p ON p.publisher_id = sgp.publisher_id
GROUP BY p.publisher_name
ORDER BY juegos DESC
LIMIT 20;

-- Q12: Top 20 publishers por owners totales
SELECT p.publisher_name,
       SUM(sg.owners_midpoint) AS total_owners,
       COUNT(*) AS juegos
FROM steam_game_publishers sgp
JOIN publishers p ON p.publisher_id = sgp.publisher_id
JOIN steam_games sg ON sg.appid = sgp.appid
GROUP BY p.publisher_name
ORDER BY total_owners DESC
LIMIT 20;

-- ============================================================================
-- FASE 2B: ANÁLISIS DE VENTAS GLOBALES (CONSOLAS)
-- ============================================================================

-- Q13: Top 20 juegos más vendidos
SELECT title, total_sales, c.console_abbrev
FROM console_games cg
LEFT JOIN consoles c ON c.console_id = cg.console_id
WHERE total_sales IS NOT NULL
ORDER BY total_sales DESC
LIMIT 20;

-- Q14: Ventas totales por generación de consola
SELECT console_generation,
       SUM(total_sales) AS ventas_totales,
       COUNT(*) AS juegos
FROM console_games
WHERE console_generation IS NOT NULL AND total_sales IS NOT NULL
GROUP BY console_generation
ORDER BY ventas_totales DESC;

-- Q15: Cuota de mercado por fabricante
SELECT console_manufacturer,
       SUM(total_sales) AS ventas_totales
FROM console_games
WHERE console_manufacturer IS NOT NULL AND total_sales IS NOT NULL
GROUP BY console_manufacturer
ORDER BY ventas_totales DESC;

-- Q16: Ventas totales por región
SELECT
    SUM(na_sales) AS total_na,
    SUM(jp_sales) AS total_jp,
    SUM(pal_sales) AS total_pal,
    SUM(other_sales) AS total_other,
    SUM(total_sales) AS total_global
FROM console_games
WHERE total_sales IS NOT NULL;

-- Q17: Preferencia regional por género (heatmap data)
SELECT g.genre_name,
       AVG(cg.na_share) AS na_share,
       AVG(cg.jp_share) AS jp_share,
       AVG(cg.pal_share) AS pal_share
FROM console_games cg
JOIN genres g ON g.genre_id = cg.genre_id
WHERE cg.total_sales IS NOT NULL AND cg.na_share IS NOT NULL
GROUP BY g.genre_name
ORDER BY g.genre_name;

-- Q18: Top 15 consolas por ventas
SELECT c.console_abbrev, c.console_full,
       SUM(cg.total_sales) AS ventas_totales,
       COUNT(*) AS juegos
FROM console_games cg
JOIN consoles c ON c.console_id = cg.console_id
WHERE cg.total_sales IS NOT NULL
GROUP BY c.console_abbrev, c.console_full
ORDER BY ventas_totales DESC
LIMIT 15;

-- Q19: Ventas medias por género
SELECT g.genre_name,
       AVG(cg.total_sales) AS venta_media,
       COUNT(*) AS juegos
FROM console_games cg
JOIN genres g ON g.genre_id = cg.genre_id
WHERE cg.total_sales IS NOT NULL
GROUP BY g.genre_name
ORDER BY venta_media DESC;

-- Q20: Critic score vs ventas (datos para scatter + correlación)
SELECT critic_score, total_sales
FROM console_games
WHERE critic_score IS NOT NULL AND total_sales IS NOT NULL;

-- Q21: Evolución ventas regionales por década
SELECT decade,
       SUM(na_sales) AS na,
       SUM(jp_sales) AS jp,
       SUM(pal_sales) AS pal,
       SUM(other_sales) AS other
FROM console_games
WHERE decade IS NOT NULL AND total_sales IS NOT NULL
GROUP BY decade
ORDER BY decade;

-- Q22: Top 15 publishers de consolas por ventas
SELECT publisher,
       SUM(total_sales) AS ventas_totales,
       COUNT(*) AS juegos
FROM console_games
WHERE publisher IS NOT NULL AND total_sales IS NOT NULL
GROUP BY publisher
ORDER BY ventas_totales DESC
LIMIT 15;

-- ============================================================================
-- FASE 3: PRODUCTO Y AUDIENCIA
-- ============================================================================

-- Q23: Top 20 géneros por cantidad de juegos (Steam)
SELECT g.genre_name, COUNT(*) AS cantidad
FROM steam_game_genres sgg
JOIN genres g ON g.genre_id = sgg.genre_id
GROUP BY g.genre_name
ORDER BY cantidad DESC
LIMIT 20;

-- Q24: Top 20 géneros por owners totales (Steam)
SELECT g.genre_name, SUM(sg.owners_midpoint) AS total_owners
FROM steam_game_genres sgg
JOIN genres g ON g.genre_id = sgg.genre_id
JOIN steam_games sg ON sg.appid = sgg.appid
GROUP BY g.genre_name
ORDER BY total_owners DESC
LIMIT 20;

-- Q25: Evolución de géneros por década (heatmap)
SELECT g.genre_name,
       CONCAT(FLOOR(sg.year / 10) * 10, 's') AS decade,
       COUNT(*) AS juegos
FROM steam_game_genres sgg
JOIN genres g ON g.genre_id = sgg.genre_id
JOIN steam_games sg ON sg.appid = sgg.appid
WHERE sg.year >= 2000
GROUP BY g.genre_name, decade
ORDER BY g.genre_name, decade;

-- Q26: Top 30 tags por votos totales
SELECT tag_name, SUM(tag_votes) AS total_votes
FROM steam_game_tags
GROUP BY tag_name
ORDER BY total_votes DESC
LIMIT 30;

-- Q27: Achievements vs Playtime (datos para scatter)
SELECT achievements, playtime_hours, price_category
FROM steam_games
WHERE achievements > 0 AND achievements <= 500
      AND playtime_hours > 0 AND playtime_hours <= 200;

-- Q28: DLC count vs Owners
SELECT dlc_count, owners_midpoint
FROM steam_games
WHERE dlc_count > 0 AND dlc_count <= 50;

-- Q29: Idiomas vs Owners (binned)
SELECT
    CASE
        WHEN num_languages = 1 THEN '1'
        WHEN num_languages BETWEEN 2 AND 3 THEN '2-3'
        WHEN num_languages BETWEEN 4 AND 5 THEN '4-5'
        WHEN num_languages BETWEEN 6 AND 10 THEN '6-10'
        WHEN num_languages BETWEEN 11 AND 20 THEN '11-20'
        ELSE '20+'
    END AS lang_bin,
    owners_midpoint
FROM steam_games
WHERE num_languages IS NOT NULL;

-- Q30: Playtime por género (top 12)
SELECT g.genre_name, sg.playtime_hours
FROM steam_game_genres sgg
JOIN genres g ON g.genre_id = sgg.genre_id
JOIN steam_games sg ON sg.appid = sgg.appid
WHERE sg.playtime_hours > 0 AND sg.playtime_hours <= 100
      AND g.genre_name IN (
          SELECT genre_name FROM (
              SELECT g2.genre_name, COUNT(*) AS cnt
              FROM steam_game_genres sgg2
              JOIN genres g2 ON g2.genre_id = sgg2.genre_id
              GROUP BY g2.genre_name
              ORDER BY cnt DESC
              LIMIT 12
          ) AS top_genres
      );

-- Q31: Matriz de correlación (columnas numéricas clave)
SELECT price, owners_midpoint, positive, negative,
       review_ratio, pct_pos_total, average_playtime_forever,
       peak_ccu, metacritic_score, num_languages, num_screenshots,
       num_movies, dlc_count, achievements, recommendations,
       num_reviews_total
FROM steam_games
WHERE owners_midpoint IS NOT NULL;

-- ============================================================================
-- FASE 4: EXPECTATIVA VS DESEMPEÑO
-- ============================================================================

-- Q32: Metacritic vs reviews de usuarios
SELECT name, metacritic_score, pct_pos_total, price_category, owners_midpoint
FROM steam_games
WHERE has_metacritic = TRUE AND metacritic_score > 0 AND pct_pos_total IS NOT NULL;

-- Q33: Metacritic binned vs owners
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
WHERE has_metacritic = TRUE AND metacritic_score > 0;

-- Q34: Gap crítica vs usuarios (divergente)
SELECT name, metacritic_score, pct_pos_total,
       (metacritic_score - pct_pos_total) AS gap
FROM steam_games
WHERE has_metacritic = TRUE
      AND metacritic_score > 0
      AND pct_pos_total IS NOT NULL
      AND num_reviews_total > 100
ORDER BY gap DESC;

-- Q35: Sentimiento - distribución de % positivas
SELECT name, pct_pos_total, num_reviews_total
FROM steam_games
WHERE num_reviews_total > 10 AND pct_pos_total IS NOT NULL;

-- Q36: Reviews recientes vs totales (tendencia)
SELECT name, pct_pos_recent, pct_pos_total,
       (pct_pos_recent - pct_pos_total) AS tendencia
FROM steam_games
WHERE num_reviews_recent > 10
      AND num_reviews_total > 50
      AND pct_pos_recent IS NOT NULL
      AND pct_pos_total IS NOT NULL;

-- Q37: Datos para índice de éxito compuesto
SELECT name, year, primary_genre, price, price_category,
       owners_midpoint, review_ratio, pct_pos_total, peak_ccu
FROM steam_games
WHERE review_ratio IS NOT NULL
      AND peak_ccu > 0
      AND owners_midpoint IS NOT NULL;

-- Q38: Critic score vs ventas (dataset consolas)
SELECT critic_score, total_sales, title
FROM console_games
WHERE critic_score IS NOT NULL AND total_sales IS NOT NULL;

-- ============================================================================
-- FASE 5: INSIGHTS ESTRATÉGICOS
-- ============================================================================

-- Q39: KPIs ejecutivos
SELECT
    (SELECT COUNT(*) FROM steam_games) AS total_steam,
    (SELECT COUNT(*) FROM console_games) AS total_consolas,
    (SELECT MIN(year) FROM steam_games WHERE year IS NOT NULL) AS min_year_steam,
    (SELECT MAX(year) FROM steam_games WHERE year IS NOT NULL) AS max_year_steam,
    (SELECT SUM(total_sales) FROM console_games WHERE total_sales IS NOT NULL) AS ventas_globales,
    (SELECT AVG(price) FROM steam_games) AS precio_medio,
    (SELECT AVG(price) FROM steam_games WHERE price > 0) AS precio_medio_pagos,
    (SELECT AVG(pct_pos_total) FROM steam_games WHERE pct_pos_total IS NOT NULL) AS sentimiento_medio;

-- Q40: Supply vs Demand por género (scatter de oportunidad)
SELECT g.genre_name,
       COUNT(*) AS oferta,
       AVG(sg.owners_midpoint) AS demanda_media,
       AVG(sg.review_ratio) AS satisfaccion_media
FROM steam_game_genres sgg
JOIN genres g ON g.genre_id = sgg.genre_id
JOIN steam_games sg ON sg.appid = sgg.appid
GROUP BY g.genre_name
HAVING COUNT(*) > 10;

-- Q41: Punto dulce de pricing (revenue estimado por rango)
SELECT
    CASE
        WHEN price BETWEEN 0.01 AND 2 THEN '0-2'
        WHEN price BETWEEN 2.01 AND 5 THEN '2-5'
        WHEN price BETWEEN 5.01 AND 10 THEN '5-10'
        WHEN price BETWEEN 10.01 AND 15 THEN '10-15'
        WHEN price BETWEEN 15.01 AND 20 THEN '15-20'
        WHEN price BETWEEN 20.01 AND 30 THEN '20-30'
        WHEN price BETWEEN 30.01 AND 40 THEN '30-40'
        WHEN price BETWEEN 40.01 AND 60 THEN '40-60'
        WHEN price > 60 THEN '60+'
    END AS price_range,
    COUNT(*) AS juegos,
    AVG(owners_midpoint) AS owners_medio,
    AVG(pct_pos_total) AS satisfaccion_media,
    AVG(price * owners_midpoint) AS revenue_estimado
FROM steam_games
WHERE price > 0 AND owners_midpoint IS NOT NULL
GROUP BY price_range
ORDER BY MIN(price);

-- Q42: Mejor mes de lanzamiento
SELECT month,
       AVG(owners_midpoint) AS owners_medio,
       AVG(pct_pos_total) AS satisfaccion_media,
       COUNT(*) AS juegos
FROM steam_games
WHERE month IS NOT NULL AND owners_midpoint IS NOT NULL
GROUP BY month
ORDER BY month;

-- Q43: Impacto de idiomas en alcance
SELECT
    CASE
        WHEN num_languages = 1 THEN '1'
        WHEN num_languages BETWEEN 2 AND 3 THEN '2-3'
        WHEN num_languages BETWEEN 4 AND 5 THEN '4-5'
        WHEN num_languages BETWEEN 6 AND 10 THEN '6-10'
        WHEN num_languages BETWEEN 11 AND 20 THEN '11-20'
        ELSE '20+'
    END AS lang_bin,
    AVG(owners_midpoint) AS owners_medio,
    COUNT(*) AS juegos
FROM steam_games
WHERE num_languages IS NOT NULL
GROUP BY lang_bin
ORDER BY MIN(num_languages);

-- Q44: Impacto de material de marketing
SELECT
    CASE WHEN num_movies = 0 THEN '0'
         WHEN num_movies = 1 THEN '1'
         WHEN num_movies = 2 THEN '2'
         WHEN num_movies = 3 THEN '3'
         WHEN num_movies = 4 THEN '4'
         ELSE '5+'
    END AS movie_bin,
    AVG(owners_midpoint) AS owners_medio
FROM steam_games
GROUP BY movie_bin
ORDER BY MIN(num_movies);

-- ============================================================================
-- QUERIES AVANZADAS (CTEs, Window Functions, Subqueries)
-- ============================================================================

-- Q45: Ranking de juegos por owners con percentil dentro de su género
SELECT sg.name, sg.primary_genre, sg.owners_midpoint,
       RANK() OVER (PARTITION BY sg.primary_genre ORDER BY sg.owners_midpoint DESC) AS rank_in_genre,
       PERCENT_RANK() OVER (PARTITION BY sg.primary_genre ORDER BY sg.owners_midpoint) AS percentile
FROM steam_games sg
WHERE sg.owners_midpoint IS NOT NULL AND sg.primary_genre IS NOT NULL;

-- Q46: Publishers con crecimiento (CTE - juegos por año por publisher)
WITH publisher_yearly AS (
    SELECT p.publisher_name, sg.year, COUNT(*) AS juegos
    FROM steam_game_publishers sgp
    JOIN publishers p ON p.publisher_id = sgp.publisher_id
    JOIN steam_games sg ON sg.appid = sgp.appid
    WHERE sg.year >= 2015
    GROUP BY p.publisher_name, sg.year
)
SELECT publisher_name,
       MIN(juegos) AS min_anual,
       MAX(juegos) AS max_anual,
       MAX(juegos) - MIN(juegos) AS crecimiento
FROM publisher_yearly
GROUP BY publisher_name
HAVING COUNT(DISTINCT year) >= 3
ORDER BY crecimiento DESC
LIMIT 20;

-- Q47: Género cruzado Steam × Consolas — ¿qué géneros venden más en digital vs retail?
SELECT g.genre_name,
       COALESCE(steam.total_owners, 0) AS steam_owners,
       COALESCE(console.total_sales, 0) AS console_sales
FROM genres g
LEFT JOIN (
    SELECT sgg.genre_id, SUM(sg.owners_midpoint) AS total_owners
    FROM steam_game_genres sgg
    JOIN steam_games sg ON sg.appid = sgg.appid
    GROUP BY sgg.genre_id
) steam ON steam.genre_id = g.genre_id
LEFT JOIN (
    SELECT cg.genre_id, SUM(cg.total_sales) AS total_sales
    FROM console_games cg
    WHERE cg.total_sales IS NOT NULL
    GROUP BY cg.genre_id
) console ON console.genre_id = g.genre_id
WHERE steam.total_owners IS NOT NULL OR console.total_sales IS NOT NULL
ORDER BY steam_owners DESC;
