-- =====================================================
-- Sales Dashboard Database Schema
-- Author: Tommy Lu
-- Description: Schema for B2B sales analytics database
-- =====================================================

-- Drop tables if they exist (for clean rebuild)
DROP TABLE IF EXISTS sales_transactions;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sales_reps;

-- =====================================================
-- CUSTOMERS TABLE
-- Stores company information and segmentation data
-- =====================================================
CREATE TABLE customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    segment VARCHAR(20) NOT NULL,  -- SMB, Mid-Market, Enterprise
    industry VARCHAR(50) NOT NULL,
    region VARCHAR(20) NOT NULL,   -- Northeast, Southeast, Midwest, Southwest, West
    state VARCHAR(2) NOT NULL,
    employee_count INTEGER,
    annual_revenue BIGINT,         -- Company's annual revenue (not our revenue from them)
    created_date DATE NOT NULL,
    
    -- Constraints
    CONSTRAINT chk_segment CHECK (segment IN ('SMB', 'Mid-Market', 'Enterprise')),
    CONSTRAINT chk_region CHECK (region IN ('Northeast', 'Southeast', 'Midwest', 'Southwest', 'West'))
);

-- =====================================================
-- PRODUCTS TABLE
-- TechFlow's product catalog with pricing
-- =====================================================
CREATE TABLE products (
    product_id VARCHAR(10) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,      -- Platform, Analytics, Integration, etc.
    base_price DECIMAL(10,2) NOT NULL,
    implementation_fee DECIMAL(10,2),
    annual_support_pct DECIMAL(4,2),    -- Annual support as % of base price
    
    CONSTRAINT chk_price CHECK (base_price > 0)
);

-- =====================================================
-- SALES_REPS TABLE
-- Sales team members with quotas and territories
-- =====================================================
CREATE TABLE sales_reps (
    rep_id VARCHAR(10) PRIMARY KEY,
    rep_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    region VARCHAR(20) NOT NULL,
    hire_date DATE NOT NULL,
    quota_annual DECIMAL(12,2) NOT NULL,  -- Annual sales quota
    manager VARCHAR(100),
    
    CONSTRAINT chk_rep_region CHECK (region IN ('Northeast', 'Southeast', 'Midwest', 'Southwest', 'West'))
);

-- =====================================================
-- SALES_TRANSACTIONS TABLE
-- All deals (won, lost, and in pipeline)
-- =====================================================
CREATE TABLE sales_transactions (
    transaction_id VARCHAR(10) PRIMARY KEY,
    customer_id VARCHAR(10) NOT NULL,
    product_id VARCHAR(10) NOT NULL,
    rep_id VARCHAR(10) NOT NULL,
    deal_value DECIMAL(12,2) NOT NULL,
    quantity INTEGER DEFAULT 1,
    discount_pct DECIMAL(4,2) DEFAULT 0,
    status VARCHAR(20) NOT NULL,        -- Closed Won, Closed Lost, Pipeline
    stage VARCHAR(20) NOT NULL,         -- Discovery, Qualification, Proposal, Negotiation, Closed
    created_date DATE NOT NULL,
    close_date DATE,                    -- NULL if not yet closed
    expected_close_date DATE,
    lead_source VARCHAR(50),            -- Website, Referral, Trade Show, etc.
    notes TEXT,
    
    -- Foreign keys
    CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_rep FOREIGN KEY (rep_id) REFERENCES sales_reps(rep_id),
    
    -- Constraints
    CONSTRAINT chk_status CHECK (status IN ('Closed Won', 'Closed Lost', 'Pipeline')),
    CONSTRAINT chk_deal_value CHECK (deal_value > 0),
    CONSTRAINT chk_discount CHECK (discount_pct >= 0 AND discount_pct <= 1)
);

-- =====================================================
-- INDEXES
-- Optimize common query patterns
-- =====================================================

-- Date-based queries for time series analysis
CREATE INDEX idx_transactions_created ON sales_transactions(created_date);
CREATE INDEX idx_transactions_closed ON sales_transactions(close_date);

-- Status filtering (very common)
CREATE INDEX idx_transactions_status ON sales_transactions(status);

-- Rep performance queries
CREATE INDEX idx_transactions_rep ON sales_transactions(rep_id);

-- Customer segment analysis
CREATE INDEX idx_customers_segment ON customers(segment);
CREATE INDEX idx_customers_region ON customers(region);

-- =====================================================
-- VIEWS
-- Pre-built queries for common analysis needs
-- =====================================================

-- View: Closed deals only (most common analysis scope)
CREATE VIEW v_closed_deals AS
SELECT 
    t.*,
    c.company_name,
    c.segment,
    c.industry,
    c.region as customer_region,
    p.product_name,
    p.category as product_category,
    r.rep_name,
    r.region as rep_region,
    r.quota_annual,
    -- Calculate sales cycle length
    JULIANDAY(t.close_date) - JULIANDAY(t.created_date) as sales_cycle_days
FROM sales_transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
JOIN sales_reps r ON t.rep_id = r.rep_id
WHERE t.status IN ('Closed Won', 'Closed Lost');

-- View: Pipeline deals
CREATE VIEW v_pipeline AS
SELECT 
    t.*,
    c.company_name,
    c.segment,
    c.industry,
    p.product_name,
    r.rep_name
FROM sales_transactions t
JOIN customers c ON t.customer_id = c.customer_id
JOIN products p ON t.product_id = p.product_id
JOIN sales_reps r ON t.rep_id = r.rep_id
WHERE t.status = 'Pipeline';

-- View: Monthly revenue summary
CREATE VIEW v_monthly_revenue AS
SELECT 
    strftime('%Y-%m', close_date) as month,
    COUNT(*) as deal_count,
    SUM(deal_value) as total_revenue,
    AVG(deal_value) as avg_deal_size,
    SUM(CASE WHEN status = 'Closed Won' THEN 1 ELSE 0 END) as won_deals,
    SUM(CASE WHEN status = 'Closed Lost' THEN 1 ELSE 0 END) as lost_deals
FROM sales_transactions
WHERE status IN ('Closed Won', 'Closed Lost')
GROUP BY strftime('%Y-%m', close_date)
ORDER BY month;
