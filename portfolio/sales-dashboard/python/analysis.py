"""
Sales Analysis Functions
Author: Tommy Lu

This module contains reusable analysis functions for the sales dashboard.
Each function returns a DataFrame that can be:
- Displayed directly in Streamlit
- Converted to charts with Plotly
- Exported to CSV/Excel

These functions abstract away the SQL so the dashboard code stays clean.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from database import execute_query, get_connection


# =============================================================================
# REVENUE ANALYSIS
# =============================================================================

def get_total_revenue() -> float:
    """
    Get total revenue from closed-won deals.
    
    Returns:
        Total revenue as float
    
    Example:
        total = get_total_revenue()
        print(f"Total Revenue: ${total:,.2f}")
    """
    query = """
        SELECT SUM(deal_value) as total_revenue
        FROM sales_transactions
        WHERE status = 'Closed Won'
    """
    result = execute_query(query)
    return result['total_revenue'].iloc[0] or 0


def get_revenue_kpis() -> dict:
    """
    Get key revenue metrics in a single query.
    
    Returns:
        Dictionary with:
        - total_revenue
        - deal_count
        - avg_deal_size
        - win_rate
    
    This is efficient because we get all KPIs in one database round-trip.
    """
    query = """
        SELECT 
            SUM(CASE WHEN status = 'Closed Won' THEN deal_value ELSE 0 END) as total_revenue,
            SUM(CASE WHEN status = 'Closed Won' THEN 1 ELSE 0 END) as deals_won,
            SUM(CASE WHEN status = 'Closed Lost' THEN 1 ELSE 0 END) as deals_lost,
            AVG(CASE WHEN status = 'Closed Won' THEN deal_value ELSE NULL END) as avg_deal_size
        FROM sales_transactions
        WHERE status IN ('Closed Won', 'Closed Lost')
    """
    result = execute_query(query)
    row = result.iloc[0]
    
    # Calculate win rate
    total_closed = row['deals_won'] + row['deals_lost']
    win_rate = (row['deals_won'] / total_closed * 100) if total_closed > 0 else 0
    
    return {
        'total_revenue': row['total_revenue'] or 0,
        'deal_count': int(row['deals_won']),
        'avg_deal_size': row['avg_deal_size'] or 0,
        'win_rate': win_rate
    }


def get_monthly_revenue() -> pd.DataFrame:
    """
    Get monthly revenue trend with month-over-month growth.
    
    Returns:
        DataFrame with columns: month, revenue, mom_growth_pct
    
    Use this for line charts showing revenue over time.
    """
    query = """
        WITH monthly_totals AS (
            SELECT 
                strftime('%Y-%m', close_date) as month,
                SUM(deal_value) as revenue
            FROM sales_transactions
            WHERE status = 'Closed Won'
            GROUP BY strftime('%Y-%m', close_date)
        )
        SELECT 
            month,
            revenue,
            LAG(revenue) OVER (ORDER BY month) as prev_month,
            ROUND(
                (revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0 / 
                NULLIF(LAG(revenue) OVER (ORDER BY month), 0),
                2
            ) as mom_growth_pct
        FROM monthly_totals
        ORDER BY month
    """
    df = execute_query(query)
    
    # Convert month string to datetime for better plotting
    df['month_date'] = pd.to_datetime(df['month'] + '-01')
    
    return df


def get_revenue_by_segment() -> pd.DataFrame:
    """
    Get revenue breakdown by customer segment.
    
    Returns:
        DataFrame with: segment, revenue, deal_count, pct_of_total
    
    Use this for pie charts or bar charts.
    """
    query = """
        SELECT 
            c.segment,
            SUM(t.deal_value) as revenue,
            COUNT(*) as deal_count,
            ROUND(
                SUM(t.deal_value) * 100.0 / 
                (SELECT SUM(deal_value) FROM sales_transactions WHERE status = 'Closed Won'),
                2
            ) as pct_of_total
        FROM sales_transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.status = 'Closed Won'
        GROUP BY c.segment
        ORDER BY revenue DESC
    """
    return execute_query(query)


def get_revenue_by_product() -> pd.DataFrame:
    """
    Get revenue breakdown by product.
    
    Returns:
        DataFrame with: product_name, category, revenue, units_sold
    """
    query = """
        SELECT 
            p.product_name,
            p.category,
            SUM(t.deal_value) as revenue,
            SUM(t.quantity) as units_sold,
            AVG(t.deal_value) as avg_price
        FROM sales_transactions t
        JOIN products p ON t.product_id = p.product_id
        WHERE t.status = 'Closed Won'
        GROUP BY p.product_id, p.product_name, p.category
        ORDER BY revenue DESC
    """
    return execute_query(query)


def get_revenue_by_region() -> pd.DataFrame:
    """
    Get revenue breakdown by geographic region.
    """
    query = """
        SELECT 
            c.region,
            SUM(t.deal_value) as revenue,
            COUNT(*) as deal_count,
            COUNT(DISTINCT c.customer_id) as unique_customers
        FROM sales_transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.status = 'Closed Won'
        GROUP BY c.region
        ORDER BY revenue DESC
    """
    return execute_query(query)


# =============================================================================
# SALES REP ANALYSIS
# =============================================================================

def get_rep_leaderboard() -> pd.DataFrame:
    """
    Get sales rep performance leaderboard.
    
    Returns:
        DataFrame with rep metrics, sorted by revenue descending
    """
    query = """
        SELECT 
            r.rep_name,
            r.region,
            r.quota_annual,
            COUNT(CASE WHEN t.status = 'Closed Won' THEN 1 END) as deals_won,
            SUM(CASE WHEN t.status = 'Closed Won' THEN t.deal_value ELSE 0 END) as total_revenue,
            AVG(CASE WHEN t.status = 'Closed Won' THEN t.deal_value END) as avg_deal_size,
            ROUND(
                COUNT(CASE WHEN t.status = 'Closed Won' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(CASE WHEN t.status IN ('Closed Won', 'Closed Lost') THEN 1 END), 0),
                2
            ) as win_rate_pct,
            ROUND(
                SUM(CASE WHEN t.status = 'Closed Won' THEN t.deal_value ELSE 0 END) * 100.0 / 
                r.quota_annual,
                2
            ) as quota_attainment_pct
        FROM sales_reps r
        LEFT JOIN sales_transactions t ON r.rep_id = t.rep_id
        GROUP BY r.rep_id, r.rep_name, r.region, r.quota_annual
        ORDER BY total_revenue DESC
    """
    return execute_query(query)


def get_rep_monthly_trend(rep_name: str = None) -> pd.DataFrame:
    """
    Get monthly revenue trend for sales reps.
    
    Args:
        rep_name: Optional - filter to specific rep
    
    Returns:
        DataFrame with monthly revenue per rep
    """
    query = """
        SELECT 
            r.rep_name,
            strftime('%Y-%m', t.close_date) as month,
            SUM(t.deal_value) as revenue,
            COUNT(*) as deals
        FROM sales_reps r
        JOIN sales_transactions t ON r.rep_id = t.rep_id
        WHERE t.status = 'Closed Won'
    """
    
    if rep_name:
        query += f" AND r.rep_name = '{rep_name}'"
    
    query += """
        GROUP BY r.rep_name, strftime('%Y-%m', t.close_date)
        ORDER BY r.rep_name, month
    """
    
    return execute_query(query)


# =============================================================================
# CUSTOMER ANALYSIS
# =============================================================================

def get_top_customers(limit: int = 10) -> pd.DataFrame:
    """
    Get top customers by lifetime value.
    
    Args:
        limit: Number of customers to return (default 10)
    
    Returns:
        DataFrame with customer metrics
    """
    query = f"""
        SELECT 
            c.company_name,
            c.segment,
            c.industry,
            COUNT(t.transaction_id) as total_purchases,
            SUM(t.deal_value) as lifetime_value,
            MIN(t.close_date) as first_purchase,
            MAX(t.close_date) as last_purchase
        FROM customers c
        JOIN sales_transactions t ON c.customer_id = t.customer_id
        WHERE t.status = 'Closed Won'
        GROUP BY c.customer_id, c.company_name, c.segment, c.industry
        ORDER BY lifetime_value DESC
        LIMIT {limit}
    """
    return execute_query(query)


def get_customer_segments_analysis() -> pd.DataFrame:
    """
    Get detailed segment analysis including deal metrics.
    """
    query = """
        SELECT 
            c.segment,
            COUNT(DISTINCT c.customer_id) as customer_count,
            COUNT(t.transaction_id) as total_deals,
            SUM(t.deal_value) as total_revenue,
            AVG(t.deal_value) as avg_deal_size,
            AVG(JULIANDAY(t.close_date) - JULIANDAY(t.created_date)) as avg_sales_cycle_days
        FROM customers c
        JOIN sales_transactions t ON c.customer_id = t.customer_id
        WHERE t.status = 'Closed Won'
        GROUP BY c.segment
        ORDER BY total_revenue DESC
    """
    return execute_query(query)


# =============================================================================
# PIPELINE ANALYSIS
# =============================================================================

def get_pipeline_summary() -> pd.DataFrame:
    """
    Get current pipeline summary by stage.
    
    Returns:
        DataFrame with pipeline stage metrics
    """
    query = """
        SELECT 
            stage,
            COUNT(*) as opportunity_count,
            SUM(deal_value) as pipeline_value,
            AVG(deal_value) as avg_opp_size
        FROM sales_transactions
        WHERE status = 'Pipeline'
        GROUP BY stage
        ORDER BY 
            CASE stage
                WHEN 'Discovery' THEN 1
                WHEN 'Qualification' THEN 2
                WHEN 'Proposal' THEN 3
                WHEN 'Negotiation' THEN 4
            END
    """
    return execute_query(query)


def get_total_pipeline_value() -> float:
    """Get total value of deals in pipeline."""
    query = """
        SELECT SUM(deal_value) as pipeline_value
        FROM sales_transactions
        WHERE status = 'Pipeline'
    """
    result = execute_query(query)
    return result['pipeline_value'].iloc[0] or 0


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_date_range() -> tuple:
    """
    Get the date range of the data.
    
    Returns:
        Tuple of (min_date, max_date) as strings
    """
    query = """
        SELECT 
            MIN(close_date) as min_date,
            MAX(close_date) as max_date
        FROM sales_transactions
        WHERE close_date IS NOT NULL
    """
    result = execute_query(query)
    return (result['min_date'].iloc[0], result['max_date'].iloc[0])


def filter_by_date_range(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Get all transactions within a date range.
    
    Useful for creating filtered views in the dashboard.
    """
    query = """
        SELECT t.*, c.company_name, c.segment, p.product_name, r.rep_name
        FROM sales_transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        JOIN products p ON t.product_id = p.product_id
        JOIN sales_reps r ON t.rep_id = t.rep_id
        WHERE t.close_date BETWEEN ? AND ?
          AND t.status = 'Closed Won'
        ORDER BY t.close_date DESC
    """
    return execute_query(query, (start_date, end_date))


# =============================================================================
# TEST / DEMO
# =============================================================================

if __name__ == "__main__":
    """
    Quick test to verify analysis functions work.
    Run: python analysis.py
    """
    print("Testing analysis functions...\n")
    
    # Test KPIs
    print("=" * 40)
    print("REVENUE KPIs")
    print("=" * 40)
    kpis = get_revenue_kpis()
    print(f"Total Revenue: ${kpis['total_revenue']:,.2f}")
    print(f"Deals Won: {kpis['deal_count']}")
    print(f"Avg Deal Size: ${kpis['avg_deal_size']:,.2f}")
    print(f"Win Rate: {kpis['win_rate']:.1f}%")
    
    # Test segment breakdown
    print("\n" + "=" * 40)
    print("REVENUE BY SEGMENT")
    print("=" * 40)
    print(get_revenue_by_segment().to_string(index=False))
    
    # Test rep leaderboard
    print("\n" + "=" * 40)
    print("SALES REP LEADERBOARD")
    print("=" * 40)
    print(get_rep_leaderboard()[['rep_name', 'total_revenue', 'win_rate_pct']].to_string(index=False))
    
    # Test pipeline
    print("\n" + "=" * 40)
    print("PIPELINE SUMMARY")
    print("=" * 40)
    print(get_pipeline_summary().to_string(index=False))
    print(f"\nTotal Pipeline Value: ${get_total_pipeline_value():,.2f}")
