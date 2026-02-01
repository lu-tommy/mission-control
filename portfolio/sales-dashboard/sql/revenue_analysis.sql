-- =====================================================
-- Revenue Analysis Queries
-- Author: Tommy Lu
-- Description: SQL queries for revenue KPIs and trends
-- =====================================================

-- =====================================================
-- 1. OVERALL REVENUE METRICS
-- Basic KPIs for executive summary
-- =====================================================

-- Total revenue from closed-won deals
SELECT 
    COUNT(*) as total_deals,
    SUM(deal_value) as total_revenue,
    AVG(deal_value) as avg_deal_size,
    MIN(deal_value) as smallest_deal,
    MAX(deal_value) as largest_deal
FROM sales_transactions
WHERE status = 'Closed Won';

-- =====================================================
-- 2. MONTHLY REVENUE TREND
-- Time series for line chart
-- =====================================================

-- Monthly revenue with month-over-month calculation
-- Note: Using LAG for MoM comparison (requires window function support)
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
    LAG(revenue) OVER (ORDER BY month) as prev_month_revenue,
    -- Calculate MoM growth percentage
    ROUND(
        (revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0 / 
        NULLIF(LAG(revenue) OVER (ORDER BY month), 0),
        2
    ) as mom_growth_pct
FROM monthly_totals
ORDER BY month;

-- =====================================================
-- 3. QUARTERLY REVENUE BREAKDOWN
-- Useful for seasonal analysis
-- =====================================================

SELECT 
    -- Extract year and quarter from close date
    strftime('%Y', close_date) as year,
    CASE 
        WHEN CAST(strftime('%m', close_date) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
        WHEN CAST(strftime('%m', close_date) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
        WHEN CAST(strftime('%m', close_date) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
        ELSE 'Q4'
    END as quarter,
    COUNT(*) as deal_count,
    SUM(deal_value) as quarterly_revenue,
    AVG(deal_value) as avg_deal_size
FROM sales_transactions
WHERE status = 'Closed Won'
GROUP BY 
    strftime('%Y', close_date),
    CASE 
        WHEN CAST(strftime('%m', close_date) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
        WHEN CAST(strftime('%m', close_date) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
        WHEN CAST(strftime('%m', close_date) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
        ELSE 'Q4'
    END
ORDER BY year, quarter;

-- =====================================================
-- 4. REVENUE BY PRODUCT
-- Identify top-selling products
-- =====================================================

SELECT 
    p.product_name,
    p.category,
    COUNT(*) as units_sold,
    SUM(t.deal_value) as total_revenue,
    AVG(t.deal_value) as avg_selling_price,
    -- Calculate what % of total revenue this product represents
    ROUND(
        SUM(t.deal_value) * 100.0 / 
        (SELECT SUM(deal_value) FROM sales_transactions WHERE status = 'Closed Won'),
        2
    ) as pct_of_revenue
FROM sales_transactions t
JOIN products p ON t.product_id = p.product_id
WHERE t.status = 'Closed Won'
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC;

-- =====================================================
-- 5. REVENUE BY REGION
-- Geographic performance analysis
-- =====================================================

SELECT 
    c.region,
    COUNT(DISTINCT c.customer_id) as unique_customers,
    COUNT(*) as total_deals,
    SUM(t.deal_value) as total_revenue,
    AVG(t.deal_value) as avg_deal_size,
    ROUND(
        SUM(t.deal_value) * 100.0 / 
        (SELECT SUM(deal_value) FROM sales_transactions WHERE status = 'Closed Won'),
        2
    ) as pct_of_revenue
FROM sales_transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'Closed Won'
GROUP BY c.region
ORDER BY total_revenue DESC;

-- =====================================================
-- 6. NEW VS EXPANSION REVENUE
-- Important for SaaS/recurring business analysis
-- =====================================================

SELECT 
    CASE 
        WHEN t.lead_source = 'Upsell' THEN 'Expansion'
        ELSE 'New Business'
    END as revenue_type,
    COUNT(*) as deal_count,
    SUM(t.deal_value) as total_revenue,
    AVG(t.deal_value) as avg_deal_size,
    ROUND(
        SUM(t.deal_value) * 100.0 / 
        (SELECT SUM(deal_value) FROM sales_transactions WHERE status = 'Closed Won'),
        2
    ) as pct_of_revenue
FROM sales_transactions t
WHERE t.status = 'Closed Won'
GROUP BY 
    CASE 
        WHEN t.lead_source = 'Upsell' THEN 'Expansion'
        ELSE 'New Business'
    END
ORDER BY total_revenue DESC;

-- =====================================================
-- 7. LEAD SOURCE PERFORMANCE
-- Marketing channel effectiveness
-- =====================================================

SELECT 
    lead_source,
    COUNT(*) as total_opportunities,
    SUM(CASE WHEN status = 'Closed Won' THEN 1 ELSE 0 END) as won_deals,
    SUM(CASE WHEN status = 'Closed Lost' THEN 1 ELSE 0 END) as lost_deals,
    -- Win rate calculation
    ROUND(
        SUM(CASE WHEN status = 'Closed Won' THEN 1 ELSE 0 END) * 100.0 / 
        COUNT(*),
        2
    ) as win_rate_pct,
    SUM(CASE WHEN status = 'Closed Won' THEN deal_value ELSE 0 END) as total_revenue,
    AVG(CASE WHEN status = 'Closed Won' THEN deal_value ELSE NULL END) as avg_won_deal
FROM sales_transactions
WHERE status IN ('Closed Won', 'Closed Lost')
GROUP BY lead_source
ORDER BY total_revenue DESC;

-- =====================================================
-- 8. CUMULATIVE REVENUE (RUNNING TOTAL)
-- For area chart or goal tracking
-- =====================================================

WITH daily_revenue AS (
    SELECT 
        close_date,
        SUM(deal_value) as daily_total
    FROM sales_transactions
    WHERE status = 'Closed Won'
    GROUP BY close_date
)
SELECT 
    close_date,
    daily_total,
    SUM(daily_total) OVER (ORDER BY close_date) as cumulative_revenue
FROM daily_revenue
ORDER BY close_date;

-- =====================================================
-- 9. DISCOUNT IMPACT ANALYSIS
-- How discounting affects deal size
-- =====================================================

SELECT 
    CASE 
        WHEN discount_pct = 0 THEN 'No Discount'
        WHEN discount_pct <= 0.05 THEN '1-5%'
        WHEN discount_pct <= 0.10 THEN '6-10%'
        ELSE '10%+'
    END as discount_range,
    COUNT(*) as deal_count,
    AVG(deal_value) as avg_deal_value,
    SUM(deal_value) as total_revenue
FROM sales_transactions
WHERE status = 'Closed Won'
GROUP BY 
    CASE 
        WHEN discount_pct = 0 THEN 'No Discount'
        WHEN discount_pct <= 0.05 THEN '1-5%'
        WHEN discount_pct <= 0.10 THEN '6-10%'
        ELSE '10%+'
    END
ORDER BY 
    CASE discount_range
        WHEN 'No Discount' THEN 1
        WHEN '1-5%' THEN 2
        WHEN '6-10%' THEN 3
        ELSE 4
    END;
