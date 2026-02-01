-- =====================================================
-- Sales Rep Performance Queries
-- Author: Tommy Lu
-- Description: SQL queries for sales team analytics
-- =====================================================

-- =====================================================
-- 1. REP PERFORMANCE LEADERBOARD
-- Core metrics for each sales rep
-- =====================================================

SELECT 
    r.rep_id,
    r.rep_name,
    r.region,
    r.quota_annual,
    -- Revenue metrics
    COUNT(CASE WHEN t.status = 'Closed Won' THEN 1 END) as deals_won,
    COUNT(CASE WHEN t.status = 'Closed Lost' THEN 1 END) as deals_lost,
    SUM(CASE WHEN t.status = 'Closed Won' THEN t.deal_value ELSE 0 END) as total_revenue,
    AVG(CASE WHEN t.status = 'Closed Won' THEN t.deal_value END) as avg_deal_size,
    -- Win rate
    ROUND(
        COUNT(CASE WHEN t.status = 'Closed Won' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(CASE WHEN t.status IN ('Closed Won', 'Closed Lost') THEN 1 END), 0),
        2
    ) as win_rate_pct,
    -- Quota attainment
    ROUND(
        SUM(CASE WHEN t.status = 'Closed Won' THEN t.deal_value ELSE 0 END) * 100.0 / 
        r.quota_annual,
        2
    ) as quota_attainment_pct
FROM sales_reps r
LEFT JOIN sales_transactions t ON r.rep_id = t.rep_id
GROUP BY r.rep_id, r.rep_name, r.region, r.quota_annual
ORDER BY total_revenue DESC;

-- =====================================================
-- 2. MONTHLY REP PERFORMANCE TREND
-- Track each rep's progress over time
-- =====================================================

SELECT 
    r.rep_name,
    strftime('%Y-%m', t.close_date) as month,
    COUNT(*) as deals_closed,
    SUM(t.deal_value) as monthly_revenue,
    -- Running total for quota tracking
    SUM(SUM(t.deal_value)) OVER (
        PARTITION BY r.rep_id 
        ORDER BY strftime('%Y-%m', t.close_date)
    ) as ytd_revenue
FROM sales_reps r
JOIN sales_transactions t ON r.rep_id = t.rep_id
WHERE t.status = 'Closed Won'
GROUP BY r.rep_id, r.rep_name, strftime('%Y-%m', t.close_date)
ORDER BY r.rep_name, month;

-- =====================================================
-- 3. SALES CYCLE ANALYSIS BY REP
-- Who closes deals fastest?
-- =====================================================

SELECT 
    r.rep_name,
    r.region,
    COUNT(*) as deals_closed,
    -- Sales cycle metrics
    ROUND(AVG(JULIANDAY(t.close_date) - JULIANDAY(t.created_date)), 1) as avg_cycle_days,
    MIN(JULIANDAY(t.close_date) - JULIANDAY(t.created_date)) as fastest_close,
    MAX(JULIANDAY(t.close_date) - JULIANDAY(t.created_date)) as slowest_close,
    -- How accurate are their forecasts?
    ROUND(AVG(JULIANDAY(t.close_date) - JULIANDAY(t.expected_close_date)), 1) as avg_days_vs_forecast
FROM sales_reps r
JOIN sales_transactions t ON r.rep_id = t.rep_id
WHERE t.status = 'Closed Won' 
  AND t.close_date IS NOT NULL 
  AND t.created_date IS NOT NULL
GROUP BY r.rep_id, r.rep_name, r.region
ORDER BY avg_cycle_days ASC;

-- =====================================================
-- 4. REP PERFORMANCE BY SEGMENT
-- Who excels with which customer types?
-- =====================================================

SELECT 
    r.rep_name,
    c.segment,
    COUNT(*) as deals_won,
    SUM(t.deal_value) as segment_revenue,
    ROUND(AVG(t.deal_value), 2) as avg_deal_size,
    -- Win rate for this segment
    ROUND(
        COUNT(*) * 100.0 / (
            SELECT COUNT(*) 
            FROM sales_transactions t2 
            JOIN customers c2 ON t2.customer_id = c2.customer_id
            WHERE t2.rep_id = r.rep_id 
              AND c2.segment = c.segment
              AND t2.status IN ('Closed Won', 'Closed Lost')
        ),
        2
    ) as segment_win_rate
FROM sales_reps r
JOIN sales_transactions t ON r.rep_id = t.rep_id
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'Closed Won'
GROUP BY r.rep_id, r.rep_name, c.segment
ORDER BY r.rep_name, segment_revenue DESC;

-- =====================================================
-- 5. PIPELINE BY REP
-- Current opportunities in progress
-- =====================================================

SELECT 
    r.rep_name,
    r.region,
    t.stage,
    COUNT(*) as opportunity_count,
    SUM(t.deal_value) as pipeline_value,
    AVG(t.deal_value) as avg_opp_size
FROM sales_reps r
JOIN sales_transactions t ON r.rep_id = t.rep_id
WHERE t.status = 'Pipeline'
GROUP BY r.rep_id, r.rep_name, r.region, t.stage
ORDER BY r.rep_name, 
    CASE t.stage
        WHEN 'Discovery' THEN 1
        WHEN 'Qualification' THEN 2
        WHEN 'Proposal' THEN 3
        WHEN 'Negotiation' THEN 4
    END;

-- =====================================================
-- 6. TOP DEALS BY REP
-- Largest wins for each salesperson
-- =====================================================

WITH ranked_deals AS (
    SELECT 
        r.rep_name,
        c.company_name,
        p.product_name,
        t.deal_value,
        t.close_date,
        ROW_NUMBER() OVER (PARTITION BY r.rep_id ORDER BY t.deal_value DESC) as deal_rank
    FROM sales_reps r
    JOIN sales_transactions t ON r.rep_id = t.rep_id
    JOIN customers c ON t.customer_id = c.customer_id
    JOIN products p ON t.product_id = p.product_id
    WHERE t.status = 'Closed Won'
)
SELECT 
    rep_name,
    company_name,
    product_name,
    deal_value,
    close_date
FROM ranked_deals
WHERE deal_rank <= 3
ORDER BY rep_name, deal_rank;

-- =====================================================
-- 7. TEAM/MANAGER ROLLUP
-- Aggregate by manager
-- =====================================================

SELECT 
    r.manager,
    COUNT(DISTINCT r.rep_id) as team_size,
    SUM(CASE WHEN t.status = 'Closed Won' THEN 1 ELSE 0 END) as total_deals_won,
    SUM(CASE WHEN t.status = 'Closed Won' THEN t.deal_value ELSE 0 END) as team_revenue,
    AVG(CASE WHEN t.status = 'Closed Won' THEN t.deal_value END) as avg_deal_size,
    -- Team quota
    SUM(r.quota_annual) as team_quota,
    -- Team attainment (avoid double-counting quota)
    ROUND(
        SUM(CASE WHEN t.status = 'Closed Won' THEN t.deal_value ELSE 0 END) * 100.0 / 
        (SELECT SUM(quota_annual) FROM sales_reps WHERE manager = r.manager),
        2
    ) as team_quota_attainment
FROM sales_reps r
LEFT JOIN sales_transactions t ON r.rep_id = t.rep_id
GROUP BY r.manager
ORDER BY team_revenue DESC;

-- =====================================================
-- 8. REP ACTIVITY METRICS
-- Deal velocity and activity level
-- =====================================================

SELECT 
    r.rep_name,
    -- Tenure in months
    ROUND((JULIANDAY('now') - JULIANDAY(r.hire_date)) / 30, 0) as tenure_months,
    -- Total activity
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN t.status = 'Closed Won' THEN 1 END) as won,
    COUNT(CASE WHEN t.status = 'Closed Lost' THEN 1 END) as lost,
    COUNT(CASE WHEN t.status = 'Pipeline' THEN 1 END) as in_pipeline,
    -- Revenue per month of tenure
    ROUND(
        SUM(CASE WHEN t.status = 'Closed Won' THEN t.deal_value ELSE 0 END) / 
        NULLIF(ROUND((JULIANDAY('now') - JULIANDAY(r.hire_date)) / 30, 0), 0),
        2
    ) as revenue_per_month
FROM sales_reps r
LEFT JOIN sales_transactions t ON r.rep_id = t.rep_id
GROUP BY r.rep_id, r.rep_name, r.hire_date
ORDER BY revenue_per_month DESC;

-- =====================================================
-- 9. DISCOUNT USAGE BY REP
-- Who discounts most heavily?
-- =====================================================

SELECT 
    r.rep_name,
    COUNT(*) as deals_won,
    ROUND(AVG(t.discount_pct) * 100, 2) as avg_discount_pct,
    SUM(CASE WHEN t.discount_pct > 0.05 THEN 1 ELSE 0 END) as heavy_discount_deals,
    -- Estimated revenue lost to discounting
    ROUND(
        SUM(t.deal_value * t.discount_pct / (1 - t.discount_pct)),
        2
    ) as estimated_discount_given
FROM sales_reps r
JOIN sales_transactions t ON r.rep_id = t.rep_id
WHERE t.status = 'Closed Won'
GROUP BY r.rep_id, r.rep_name
ORDER BY avg_discount_pct DESC;

-- =====================================================
-- 10. REP REGION ALIGNMENT
-- Are reps selling in their assigned territories?
-- =====================================================

SELECT 
    r.rep_name,
    r.region as assigned_region,
    c.region as customer_region,
    COUNT(*) as deals,
    SUM(t.deal_value) as revenue,
    CASE 
        WHEN r.region = c.region THEN 'In Territory'
        ELSE 'Outside Territory'
    END as territory_alignment
FROM sales_reps r
JOIN sales_transactions t ON r.rep_id = t.rep_id
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'Closed Won'
GROUP BY r.rep_id, r.rep_name, r.region, c.region
ORDER BY r.rep_name, revenue DESC;
