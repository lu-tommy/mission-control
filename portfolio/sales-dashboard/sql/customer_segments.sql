-- =====================================================
-- Customer Segmentation Analysis Queries
-- Author: Tommy Lu
-- Description: SQL queries for customer segment insights
-- =====================================================

-- =====================================================
-- 1. SEGMENT OVERVIEW
-- High-level breakdown by customer size
-- =====================================================

SELECT 
    c.segment,
    COUNT(DISTINCT c.customer_id) as customer_count,
    COUNT(t.transaction_id) as total_deals,
    SUM(t.deal_value) as total_revenue,
    AVG(t.deal_value) as avg_deal_size,
    -- Revenue per customer
    ROUND(SUM(t.deal_value) * 1.0 / COUNT(DISTINCT c.customer_id), 2) as revenue_per_customer,
    -- Percentage of total revenue
    ROUND(
        SUM(t.deal_value) * 100.0 / 
        (SELECT SUM(deal_value) FROM sales_transactions WHERE status = 'Closed Won'),
        2
    ) as pct_of_revenue
FROM customers c
JOIN sales_transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'Closed Won'
GROUP BY c.segment
ORDER BY total_revenue DESC;

-- =====================================================
-- 2. INDUSTRY BREAKDOWN
-- Which industries generate most revenue
-- =====================================================

SELECT 
    c.industry,
    COUNT(DISTINCT c.customer_id) as customer_count,
    SUM(t.deal_value) as total_revenue,
    AVG(t.deal_value) as avg_deal_size,
    -- Which segment dominates this industry
    (
        SELECT segment 
        FROM customers c2 
        JOIN sales_transactions t2 ON c2.customer_id = t2.customer_id
        WHERE c2.industry = c.industry AND t2.status = 'Closed Won'
        GROUP BY segment
        ORDER BY SUM(t2.deal_value) DESC
        LIMIT 1
    ) as dominant_segment
FROM customers c
JOIN sales_transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'Closed Won'
GROUP BY c.industry
ORDER BY total_revenue DESC
LIMIT 10;

-- =====================================================
-- 3. CUSTOMER LIFETIME VALUE (SIMPLE)
-- Total revenue per customer
-- =====================================================

SELECT 
    c.customer_id,
    c.company_name,
    c.segment,
    c.industry,
    COUNT(t.transaction_id) as total_purchases,
    SUM(t.deal_value) as lifetime_value,
    AVG(t.deal_value) as avg_order_value,
    MIN(t.close_date) as first_purchase,
    MAX(t.close_date) as last_purchase,
    -- Calculate customer tenure in days
    JULIANDAY(MAX(t.close_date)) - JULIANDAY(MIN(t.close_date)) as customer_tenure_days
FROM customers c
JOIN sales_transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'Closed Won'
GROUP BY c.customer_id, c.company_name, c.segment, c.industry
ORDER BY lifetime_value DESC
LIMIT 20;

-- =====================================================
-- 4. SEGMENT × PRODUCT MATRIX
-- Which products sell best to which segments
-- =====================================================

SELECT 
    c.segment,
    p.product_name,
    COUNT(*) as units_sold,
    SUM(t.deal_value) as revenue,
    ROUND(AVG(t.deal_value), 2) as avg_price
FROM sales_transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
WHERE t.status = 'Closed Won'
GROUP BY c.segment, p.product_name
ORDER BY c.segment, revenue DESC;

-- =====================================================
-- 5. CUSTOMER COHORT ANALYSIS
-- When did customers first buy?
-- =====================================================

WITH first_purchase AS (
    SELECT 
        customer_id,
        MIN(close_date) as first_purchase_date
    FROM sales_transactions
    WHERE status = 'Closed Won'
    GROUP BY customer_id
)
SELECT 
    strftime('%Y-%m', fp.first_purchase_date) as cohort_month,
    COUNT(DISTINCT fp.customer_id) as new_customers,
    SUM(t.deal_value) as cohort_revenue,
    AVG(t.deal_value) as avg_first_purchase
FROM first_purchase fp
JOIN sales_transactions t ON fp.customer_id = t.customer_id 
    AND fp.first_purchase_date = t.close_date
WHERE t.status = 'Closed Won'
GROUP BY strftime('%Y-%m', fp.first_purchase_date)
ORDER BY cohort_month;

-- =====================================================
-- 6. REPEAT CUSTOMERS VS ONE-TIME
-- Customer retention indicator
-- =====================================================

WITH customer_purchases AS (
    SELECT 
        customer_id,
        COUNT(*) as purchase_count
    FROM sales_transactions
    WHERE status = 'Closed Won'
    GROUP BY customer_id
)
SELECT 
    CASE 
        WHEN cp.purchase_count = 1 THEN 'One-Time'
        WHEN cp.purchase_count = 2 THEN 'Repeat (2x)'
        ELSE 'Loyal (3+)'
    END as customer_type,
    COUNT(DISTINCT cp.customer_id) as customer_count,
    SUM(t.deal_value) as total_revenue,
    AVG(t.deal_value) as avg_deal_value,
    ROUND(
        COUNT(DISTINCT cp.customer_id) * 100.0 / 
        (SELECT COUNT(DISTINCT customer_id) FROM sales_transactions WHERE status = 'Closed Won'),
        2
    ) as pct_of_customers
FROM customer_purchases cp
JOIN sales_transactions t ON cp.customer_id = t.customer_id
WHERE t.status = 'Closed Won'
GROUP BY 
    CASE 
        WHEN cp.purchase_count = 1 THEN 'One-Time'
        WHEN cp.purchase_count = 2 THEN 'Repeat (2x)'
        ELSE 'Loyal (3+)'
    END
ORDER BY 
    CASE customer_type
        WHEN 'One-Time' THEN 1
        WHEN 'Repeat (2x)' THEN 2
        ELSE 3
    END;

-- =====================================================
-- 7. COMPANY SIZE CORRELATION
-- Does employee count/revenue correlate with deal size?
-- =====================================================

SELECT 
    c.segment,
    -- Bucket by employee count
    CASE 
        WHEN c.employee_count < 100 THEN 'Small (<100)'
        WHEN c.employee_count < 500 THEN 'Medium (100-499)'
        WHEN c.employee_count < 2000 THEN 'Large (500-1999)'
        ELSE 'Enterprise (2000+)'
    END as company_size,
    COUNT(*) as deal_count,
    AVG(t.deal_value) as avg_deal_value,
    AVG(c.annual_revenue / 1000000.0) as avg_company_revenue_millions
FROM customers c
JOIN sales_transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'Closed Won'
GROUP BY 
    c.segment,
    CASE 
        WHEN c.employee_count < 100 THEN 'Small (<100)'
        WHEN c.employee_count < 500 THEN 'Medium (100-499)'
        WHEN c.employee_count < 2000 THEN 'Large (500-1999)'
        ELSE 'Enterprise (2000+)'
    END
ORDER BY c.segment, avg_deal_value DESC;

-- =====================================================
-- 8. GEOGRAPHIC CUSTOMER DISTRIBUTION
-- State-level analysis
-- =====================================================

SELECT 
    c.region,
    c.state,
    c.segment,
    COUNT(DISTINCT c.customer_id) as customers,
    SUM(t.deal_value) as total_revenue
FROM customers c
JOIN sales_transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'Closed Won'
GROUP BY c.region, c.state, c.segment
ORDER BY total_revenue DESC;

-- =====================================================
-- 9. CROSS-SELL OPPORTUNITIES
-- Customers who bought one product but not another
-- =====================================================

-- Find customers who bought Core Platform but not Analytics Suite
SELECT 
    c.customer_id,
    c.company_name,
    c.segment,
    SUM(t.deal_value) as current_spend
FROM customers c
JOIN sales_transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'Closed Won'
  AND t.product_id = 'P001'  -- Bought Core Platform
  AND c.customer_id NOT IN (
      SELECT customer_id 
      FROM sales_transactions 
      WHERE product_id = 'P002'  -- But NOT Analytics Suite
        AND status = 'Closed Won'
  )
GROUP BY c.customer_id, c.company_name, c.segment
ORDER BY current_spend DESC;

-- =====================================================
-- 10. SEGMENT GROWTH OVER TIME
-- How each segment is trending
-- =====================================================

SELECT 
    strftime('%Y-%m', t.close_date) as month,
    c.segment,
    COUNT(*) as deals,
    SUM(t.deal_value) as revenue
FROM sales_transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'Closed Won'
GROUP BY strftime('%Y-%m', t.close_date), c.segment
ORDER BY month, segment;
