"""
utils/db_connection.py — Módulo de conexión a MySQL
Pipeline: CSV → Python → MySQL → SQL → Pandas → NumPy → Matplotlib

Proporciona funciones para conectarse a MySQL (XAMPP/MariaDB),
ejecutar queries, y convertir resultados a DataFrames de Pandas.
"""

import os
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_PROJECT_ROOT, '.env'))

def get_db_credentials():
    """Obtiene las credenciales desde Streamlit Secrets (si está en la nube) o desde .env / os.environ (si está local)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DB_HOST" in st.secrets:
            return {
                'host': str(st.secrets["DB_HOST"]),
                'port': int(st.secrets.get("DB_PORT", 3306)),
                'user': str(st.secrets["DB_USER"]),
                'password': str(st.secrets["DB_PASSWORD"]),
                'database': str(st.secrets.get("DB_NAME", "defaultdb")),
            }
    except Exception:
        pass

    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'videogame_market_analysis'),
    }


def get_connection(use_database=True):
    """
    Obtiene una conexión a MySQL (compatible con local XAMPP y Aiven Cloud).
    """
    creds = get_db_credentials()
    config = {
        'host': creds['host'],
        'port': creds['port'],
        'user': creds['user'],
        'password': creds['password'],
    }
    if use_database:
        config['database'] = creds['database']
    
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except Error as e:
        print(f"Error de conexión a MySQL: {e}")
        print("Asegúrate de que MySQL/XAMPP esté corriendo.")
        raise


def execute_query(query, params=None, use_database=True):
    """
    Ejecuta una query SQL (INSERT, UPDATE, DELETE, CREATE, etc.).
    
    Args:
        query: String SQL a ejecutar.
        params: Tupla o lista de parámetros para query parametrizada.
        use_database: Si usar la base de datos del proyecto.
    
    Returns:
        int: Número de filas afectadas.
    """
    conn = get_connection(use_database=use_database)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def execute_many(query, data, use_database=True):
    """
    Ejecuta una query parametrizada con múltiples filas (bulk insert).
    
    Args:
        query: String SQL con placeholders %s.
        data: Lista de tuplas con los valores.
        use_database: Si usar la base de datos del proyecto.
    
    Returns:
        int: Número de filas insertadas.
    """
    conn = get_connection(use_database=use_database)
    cursor = conn.cursor()
    try:
        cursor.executemany(query, data)
        conn.commit()
        return cursor.rowcount
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def execute_script(filepath, use_database=True):
    """
    Ejecuta un archivo .sql completo (múltiples statements).
    
    Args:
        filepath: Ruta al archivo .sql.
        use_database: Si usar la base de datos del proyecto.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    conn = get_connection(use_database=use_database)
    cursor = conn.cursor()
    try:
        # Ejecutar cada statement separado por ;
        for statement in sql_script.split(';'):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def query_to_dataframe(query, params=None):
    """
    Ejecuta un SELECT y devuelve el resultado como DataFrame de Pandas.
    
    Esta es la función principal del pipeline:
    MySQL → Pandas DataFrame → análisis con NumPy → visualización
    
    Args:
        query: String SQL SELECT.
        params: Tupla o lista de parámetros opcionales.
    
    Returns:
        pd.DataFrame con los resultados de la consulta.
    """
    conn = get_connection(use_database=True)
    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    finally:
        conn.close()


def get_table_count(table_name):
    """Devuelve el número de filas en una tabla."""
    df = query_to_dataframe(f"SELECT COUNT(*) AS total FROM {table_name}")
    return df['total'].iloc[0]


def table_exists(table_name):
    """Verifica si una tabla existe en la base de datos."""
    conn = get_connection(use_database=True)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


def print_db_summary():
    """Imprime un resumen de todas las tablas y sus conteos."""
    conn = get_connection(use_database=True)
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n{'='*50}")
        print(f"  Base de datos: {DB_NAME}")
        print(f"{'='*50}")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:30s} → {count:>10,} filas")
        
        print(f"{'='*50}\n")
    finally:
        cursor.close()
        conn.close()
