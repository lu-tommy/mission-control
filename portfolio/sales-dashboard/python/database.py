"""
Database Connection Utilities
Author: Tommy Lu

This module handles all database connections and provides utility functions
for executing queries. Using SQLite for simplicity, but the code is structured
to easily swap in PostgreSQL or another database.

Why this matters:
- Centralizes DB connection logic in one place
- Makes it easy to switch databases later
- Provides consistent error handling
"""

import sqlite3
import pandas as pd
from pathlib import Path
from contextlib import contextmanager


# =============================================================================
# Configuration
# =============================================================================

# Database file location (relative to project root)
# Using SQLite for portability - no server setup required
DB_PATH = Path(__file__).parent.parent / "data" / "sales_dashboard.db"


# =============================================================================
# Connection Management
# =============================================================================

@contextmanager
def get_connection():
    """
    Context manager for database connections.
    
    Usage:
        with get_connection() as conn:
            df = pd.read_sql(query, conn)
    
    Why context manager?
    - Automatically handles closing connections
    - Ensures cleanup even if errors occur
    - Prevents connection leaks
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        # Enable foreign keys (off by default in SQLite)
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        if conn:
            conn.close()


def get_engine():
    """
    Get SQLAlchemy engine for pandas operations.
    
    Some pandas functions work better with SQLAlchemy engines
    than raw sqlite3 connections.
    """
    from sqlalchemy import create_engine
    return create_engine(f"sqlite:///{DB_PATH}")


# =============================================================================
# Query Execution Helpers
# =============================================================================

def execute_query(query: str, params: tuple = None) -> pd.DataFrame:
    """
    Execute a SELECT query and return results as DataFrame.
    
    Args:
        query: SQL SELECT statement
        params: Optional tuple of parameters for parameterized queries
    
    Returns:
        pandas DataFrame with query results
    
    Example:
        df = execute_query(
            "SELECT * FROM customers WHERE segment = ?",
            ("Enterprise",)
        )
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn, params=params)


def execute_write(query: str, params: tuple = None) -> int:
    """
    Execute an INSERT/UPDATE/DELETE query.
    
    Args:
        query: SQL modification statement
        params: Optional tuple of parameters
    
    Returns:
        Number of rows affected
    
    Note: For bulk inserts, use load_dataframe() instead - it's much faster.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.rowcount


def execute_script(script_path: str) -> None:
    """
    Execute a SQL script file (multiple statements).
    
    Useful for running schema creation or data migration scripts.
    
    Args:
        script_path: Path to .sql file
    """
    with open(script_path, 'r') as f:
        script = f.read()
    
    with get_connection() as conn:
        conn.executescript(script)
        conn.commit()


# =============================================================================
# DataFrame Operations
# =============================================================================

def load_dataframe(df: pd.DataFrame, table_name: str, if_exists: str = 'append') -> int:
    """
    Load a pandas DataFrame into a database table.
    
    Args:
        df: DataFrame to load
        table_name: Target table name
        if_exists: What to do if table exists ('fail', 'replace', 'append')
    
    Returns:
        Number of rows inserted
    
    Example:
        df = pd.read_csv('customers.csv')
        rows = load_dataframe(df, 'customers', if_exists='replace')
        print(f"Loaded {rows} rows")
    """
    engine = get_engine()
    rows_before = 0
    
    # Get current row count if appending
    if if_exists == 'append':
        try:
            with get_connection() as conn:
                result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                rows_before = result.fetchone()[0]
        except:
            pass  # Table might not exist yet
    
    # Load the data
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    
    # Return rows inserted
    with get_connection() as conn:
        result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        rows_after = result.fetchone()[0]
    
    return rows_after - rows_before if if_exists == 'append' else rows_after


# =============================================================================
# Utility Functions
# =============================================================================

def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None


def get_table_info(table_name: str) -> pd.DataFrame:
    """
    Get schema information for a table.
    
    Useful for debugging and documentation.
    """
    return execute_query(f"PRAGMA table_info({table_name})")


def get_row_count(table_name: str) -> int:
    """Get the number of rows in a table."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


def init_database():
    """
    Initialize the database with schema.
    
    Run this once to set up tables. Safe to run multiple times
    (drops and recreates tables).
    """
    schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
    print(f"Initializing database from {schema_path}...")
    execute_script(str(schema_path))
    print("Database initialized successfully!")


# =============================================================================
# Main - Test connection
# =============================================================================

if __name__ == "__main__":
    """
    Quick test to verify database connection works.
    Run: python database.py
    """
    print(f"Database path: {DB_PATH}")
    print(f"Database exists: {DB_PATH.exists()}")
    
    if DB_PATH.exists():
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {[t[0] for t in tables]}")
    else:
        print("Database not found. Run etl_pipeline.py first to create it.")
