-- ============================================================================
-- schema.sql — Esquema relacional para el análisis del mercado de videojuegos
-- Base de datos: videogame_market_analysis
-- Pipeline: CSV → Python (limpieza) → MySQL → SQL queries → Pandas
-- ============================================================================

CREATE DATABASE IF NOT EXISTS videogame_market_analysis
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE videogame_market_analysis;

-- ============================================================================
-- TABLAS CATÁLOGO (dimensiones)
-- ============================================================================

-- Catálogo de géneros (compartido entre Steam y Consolas)
CREATE TABLE IF NOT EXISTS genres (
    genre_id    INT AUTO_INCREMENT PRIMARY KEY,
    genre_name  VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Catálogo de publishers
CREATE TABLE IF NOT EXISTS publishers (
    publisher_id    INT AUTO_INCREMENT PRIMARY KEY,
    publisher_name  VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Catálogo de consolas (para dataset de ventas)
CREATE TABLE IF NOT EXISTS consoles (
    console_id          INT AUTO_INCREMENT PRIMARY KEY,
    console_abbrev      VARCHAR(50) NOT NULL UNIQUE,
    console_full        VARCHAR(150),
    console_generation  VARCHAR(50),
    console_manufacturer VARCHAR(100)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLA PRINCIPAL: STEAM GAMES (hechos)
-- ============================================================================

CREATE TABLE IF NOT EXISTS steam_games (
    appid                   INT PRIMARY KEY,
    name                    VARCHAR(500) NOT NULL,
    year                    INT,
    month                   INT,
    price                   DECIMAL(10,2),
    price_category          VARCHAR(20),
    is_free                 BOOLEAN DEFAULT FALSE,
    owners_min              BIGINT,
    owners_max              BIGINT,
    owners_midpoint         BIGINT,
    popularity_tier         VARCHAR(50),
    positive                INT DEFAULT 0,
    negative                INT DEFAULT 0,
    review_ratio            FLOAT,
    pct_pos_total           FLOAT,
    pct_pos_recent          FLOAT,
    num_reviews_total       INT DEFAULT 0,
    num_reviews_recent      INT DEFAULT 0,
    average_playtime_forever INT DEFAULT 0,
    playtime_hours          FLOAT,
    peak_ccu                INT DEFAULT 0,
    metacritic_score        INT,
    has_metacritic           BOOLEAN DEFAULT FALSE,
    num_languages           INT DEFAULT 1,
    num_screenshots         INT DEFAULT 0,
    num_movies              INT DEFAULT 0,
    dlc_count               INT DEFAULT 0,
    achievements            INT DEFAULT 0,
    recommendations         INT DEFAULT 0,
    windows                 BOOLEAN DEFAULT TRUE,
    mac                     BOOLEAN DEFAULT FALSE,
    linux                   BOOLEAN DEFAULT FALSE,
    primary_genre           VARCHAR(100),

    INDEX idx_year (year),
    INDEX idx_price (price),
    INDEX idx_price_category (price_category),
    INDEX idx_owners (owners_midpoint),
    INDEX idx_primary_genre (primary_genre),
    INDEX idx_metacritic (metacritic_score),
    INDEX idx_peak_ccu (peak_ccu)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLAS INTERMEDIAS M:N (Steam)
-- ============================================================================

-- Relación muchos-a-muchos: juegos ↔ géneros
CREATE TABLE IF NOT EXISTS steam_game_genres (
    appid       INT NOT NULL,
    genre_id    INT NOT NULL,
    PRIMARY KEY (appid, genre_id),
    FOREIGN KEY (appid) REFERENCES steam_games(appid) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tags con votos (relación juego → tag con peso)
CREATE TABLE IF NOT EXISTS steam_game_tags (
    appid       INT NOT NULL,
    tag_name    VARCHAR(200) NOT NULL,
    tag_votes   INT DEFAULT 0,
    PRIMARY KEY (appid, tag_name),
    FOREIGN KEY (appid) REFERENCES steam_games(appid) ON DELETE CASCADE,
    INDEX idx_tag_name (tag_name)
) ENGINE=InnoDB;

-- Relación muchos-a-muchos: juegos ↔ publishers
CREATE TABLE IF NOT EXISTS steam_game_publishers (
    appid           INT NOT NULL,
    publisher_id    INT NOT NULL,
    PRIMARY KEY (appid, publisher_id),
    FOREIGN KEY (appid) REFERENCES steam_games(appid) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Relación muchos-a-muchos: juegos ↔ developers
CREATE TABLE IF NOT EXISTS steam_game_developers (
    appid           INT NOT NULL,
    developer_name  VARCHAR(255) NOT NULL,
    PRIMARY KEY (appid, developer_name),
    FOREIGN KEY (appid) REFERENCES steam_games(appid) ON DELETE CASCADE,
    INDEX idx_developer (developer_name)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLA PRINCIPAL: CONSOLE GAMES / VENTAS (hechos)
-- ============================================================================

CREATE TABLE IF NOT EXISTS console_games (
    game_id             INT AUTO_INCREMENT PRIMARY KEY,
    title               VARCHAR(500) NOT NULL,
    console_id          INT,
    genre_id            INT,
    publisher           VARCHAR(255),
    developer           VARCHAR(255),
    critic_score        FLOAT,
    total_sales         FLOAT,
    na_sales            FLOAT,
    jp_sales            FLOAT,
    pal_sales           FLOAT,
    other_sales         FLOAT,
    release_date        DATE,
    year                INT,
    decade              VARCHAR(10),
    dominant_region     VARCHAR(10),
    na_share            FLOAT,
    jp_share            FLOAT,
    pal_share           FLOAT,
    other_share         FLOAT,
    console_generation  VARCHAR(50),
    console_manufacturer VARCHAR(100),

    FOREIGN KEY (console_id) REFERENCES consoles(console_id) ON DELETE SET NULL,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE SET NULL,

    INDEX idx_title (title(100)),
    INDEX idx_year (year),
    INDEX idx_genre (genre_id),
    INDEX idx_console (console_id),
    INDEX idx_total_sales (total_sales),
    INDEX idx_critic_score (critic_score)
) ENGINE=InnoDB;
