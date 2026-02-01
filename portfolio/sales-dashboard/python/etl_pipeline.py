"""
ETL Pipeline for Sales Dashboard
Author: Tommy Lu

This script handles the Extract-Transform-Load process:
1. EXTRACT: Read raw CSV files from data/raw/
2. TRANSFORM: Clean, validate, and enrich the data
3. LOAD: Insert into SQLite database

Run this script to rebuild the database from source CSVs.

Usage:
    python etl_pipeline.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from database import (
    init_database, load_dataframe, get_row_count, 
    get_connection, DB_PATH
)


# =============================================================================
# Configuration
# =============================================================================

# Paths
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DATA_DIR = Path(__file__).parent.parent / "data" / "processed"

# Ensure processed directory exists
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# EXTRACT: Load Raw Data
# =============================================================================

def extract_customers() -> pd.DataFrame:
    """
    Load customer data from CSV.
    
    Returns DataFrame with all customer records.
    """
    print("  Loading customers.csv...")
    df = pd.read_csv(RAW_DATA_DIR / "customers.csv")
    print(f"    Loaded {len(df)} customers")
    return df


def extract_products() -> pd.DataFrame:
    """Load product catalog from CSV."""
    print("  Loading products.csv...")
    df = pd.read_csv(RAW_DATA_DIR / "products.csv")
    print(f"    Loaded {len(df)} products")
    return df


def extract_sales_reps() -> pd.DataFrame:
    """Load sales rep data from CSV."""
    print("  Loading sales_reps.csv...")
    df = pd.read_csv(RAW_DATA_DIR / "sales_reps.csv")
    print(f"    Loaded {len(df)} sales reps")
    return df


def extract_transactions() -> pd.DataFrame:
    """Load sales transactions from CSV."""
    print("  Loading sales_transactions.csv...")
    df = pd.read_csv(RAW_DATA_DIR / "sales_transactions.csv")
    print(f"    Loaded {len(df)} transactions")
    return df


# =============================================================================
# TRANSFORM: Clean and Validate Data
# =============================================================================

def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform customer data.
    
    Transformations:
    - Convert dates to datetime
    - Validate segment values
    - Clean company names (trim whitespace)
    """
    print("  Transforming customers...")
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Convert date columns
    df['created_date'] = pd.to_datetime(df['created_date'])
    
    # Clean text fields
    df['company_name'] = df['company_name'].str.strip()
    df['segment'] = df['segment'].str.strip()
    df['industry'] = df['industry'].str.strip()
    
    # Validate segments
    valid_segments = {'SMB', 'Mid-Market', 'Enterprise'}
    invalid = df[~df['segment'].isin(valid_segments)]
    if len(invalid) > 0:
        print(f"    WARNING: {len(invalid)} records with invalid segments")
    
    print(f"    Transformed {len(df)} customers")
    return df


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform product data.
    
    Transformations:
    - Ensure price columns are numeric
    - Calculate full price (base + implementation)
    """
    print("  Transforming products...")
    
    df = df.copy()
    
    # Ensure numeric types
    df['base_price'] = pd.to_numeric(df['base_price'], errors='coerce')
    df['implementation_fee'] = pd.to_numeric(df['implementation_fee'], errors='coerce')
    df['annual_support_pct'] = pd.to_numeric(df['annual_support_pct'], errors='coerce')
    
    # Check for any parsing errors
    null_prices = df['base_price'].isna().sum()
    if null_prices > 0:
        print(f"    WARNING: {null_prices} products with invalid prices")
    
    print(f"    Transformed {len(df)} products")
    return df


def transform_sales_reps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform sales rep data.
    
    Transformations:
    - Convert hire_date to datetime
    - Validate email format (basic check)
    - Ensure quota is numeric
    """
    print("  Transforming sales reps...")
    
    df = df.copy()
    
    # Convert dates
    df['hire_date'] = pd.to_datetime(df['hire_date'])
    
    # Clean text
    df['rep_name'] = df['rep_name'].str.strip()
    df['email'] = df['email'].str.strip().str.lower()
    
    # Ensure quota is numeric
    df['quota_annual'] = pd.to_numeric(df['quota_annual'], errors='coerce')
    
    # Basic email validation
    invalid_emails = df[~df['email'].str.contains('@', na=False)]
    if len(invalid_emails) > 0:
        print(f"    WARNING: {len(invalid_emails)} reps with invalid emails")
    
    print(f"    Transformed {len(df)} sales reps")
    return df


def transform_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform sales transactions.
    
    This is the most complex transformation because transactions
    reference other tables and have multiple date fields.
    
    Transformations:
    - Convert all date columns
    - Validate foreign key references
    - Calculate derived fields (e.g., sales cycle length)
    - Handle NULL close_dates for pipeline deals
    """
    print("  Transforming transactions...")
    
    df = df.copy()
    
    # Convert date columns (close_date can be null for pipeline deals)
    df['created_date'] = pd.to_datetime(df['created_date'])
    df['close_date'] = pd.to_datetime(df['close_date'], errors='coerce')
    df['expected_close_date'] = pd.to_datetime(df['expected_close_date'], errors='coerce')
    
    # Ensure numeric fields
    df['deal_value'] = pd.to_numeric(df['deal_value'], errors='coerce')
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(1).astype(int)
    df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0)
    
    # Clean text fields
    df['status'] = df['status'].str.strip()
    df['stage'] = df['stage'].str.strip()
    df['lead_source'] = df['lead_source'].str.strip()
    
    # Validate status values
    valid_statuses = {'Closed Won', 'Closed Lost', 'Pipeline'}
    invalid_status = df[~df['status'].isin(valid_statuses)]
    if len(invalid_status) > 0:
        print(f"    WARNING: {len(invalid_status)} records with invalid status")
    
    # Validate: closed deals should have close_date
    closed_no_date = df[(df['status'].isin(['Closed Won', 'Closed Lost'])) & 
                        (df['close_date'].isna())]
    if len(closed_no_date) > 0:
        print(f"    WARNING: {len(closed_no_date)} closed deals missing close_date")
    
    print(f"    Transformed {len(df)} transactions")
    return df


# =============================================================================
# LOAD: Insert into Database
# =============================================================================

def load_to_database(customers_df, products_df, reps_df, transactions_df):
    """
    Load all transformed dataframes into the database.
    
    Order matters! We need to load reference tables (customers, products, reps)
    before transactions because of foreign key constraints.
    """
    print("\n" + "="*50)
    print("LOADING DATA TO DATABASE")
    print("="*50)
    
    # Initialize database (creates tables)
    init_database()
    
    # Load in order of dependencies
    # (Parent tables first, then child tables)
    
    print("\nLoading customers...")
    load_dataframe(customers_df, 'customers', if_exists='replace')
    print(f"  Loaded {get_row_count('customers')} customers")
    
    print("\nLoading products...")
    load_dataframe(products_df, 'products', if_exists='replace')
    print(f"  Loaded {get_row_count('products')} products")
    
    print("\nLoading sales_reps...")
    load_dataframe(reps_df, 'sales_reps', if_exists='replace')
    print(f"  Loaded {get_row_count('sales_reps')} sales reps")
    
    print("\nLoading sales_transactions...")
    load_dataframe(transactions_df, 'sales_transactions', if_exists='replace')
    print(f"  Loaded {get_row_count('sales_transactions')} transactions")


# =============================================================================
# Export Processed Data (Optional)
# =============================================================================

def export_processed_data(customers_df, products_df, reps_df, transactions_df):
    """
    Save transformed data to processed/ folder as CSVs.
    
    Useful for:
    - Debugging transformations
    - Sharing cleaned data without database
    - Power BI direct import
    """
    print("\nExporting processed data...")
    
    customers_df.to_csv(PROCESSED_DATA_DIR / "customers_clean.csv", index=False)
    products_df.to_csv(PROCESSED_DATA_DIR / "products_clean.csv", index=False)
    reps_df.to_csv(PROCESSED_DATA_DIR / "sales_reps_clean.csv", index=False)
    transactions_df.to_csv(PROCESSED_DATA_DIR / "transactions_clean.csv", index=False)
    
    print(f"  Exported to {PROCESSED_DATA_DIR}")


# =============================================================================
# Main ETL Pipeline
# =============================================================================

def run_etl():
    """
    Main ETL function - orchestrates the entire pipeline.
    
    This is the entry point. Call this to rebuild the database
    from raw CSV files.
    """
    start_time = datetime.now()
    
    print("="*50)
    print("SALES DASHBOARD ETL PIPELINE")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # ----- EXTRACT -----
    print("\n" + "-"*50)
    print("EXTRACT: Loading raw data")
    print("-"*50)
    
    customers_raw = extract_customers()
    products_raw = extract_products()
    reps_raw = extract_sales_reps()
    transactions_raw = extract_transactions()
    
    # ----- TRANSFORM -----
    print("\n" + "-"*50)
    print("TRANSFORM: Cleaning and validating")
    print("-"*50)
    
    customers_clean = transform_customers(customers_raw)
    products_clean = transform_products(products_raw)
    reps_clean = transform_sales_reps(reps_raw)
    transactions_clean = transform_transactions(transactions_raw)
    
    # ----- LOAD -----
    load_to_database(
        customers_clean, 
        products_clean, 
        reps_clean, 
        transactions_clean
    )
    
    # ----- EXPORT (Optional) -----
    export_processed_data(
        customers_clean,
        products_clean,
        reps_clean,
        transactions_clean
    )
    
    # ----- SUMMARY -----
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*50)
    print("ETL COMPLETE")
    print("="*50)
    print(f"Database: {DB_PATH}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    run_etl()
