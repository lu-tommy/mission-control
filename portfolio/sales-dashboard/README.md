# Sales Performance Dashboard 📊

A comprehensive B2B sales analytics dashboard that visualizes revenue trends, KPIs, and customer segmentation insights. Built to demonstrate data engineering and analytics skills.

![Dashboard Preview](docs/screenshots/dashboard-preview.png)
*Screenshot placeholder - add your own after building*

## 🎯 Project Overview

This project analyzes fictional B2B sales data for **TechFlow Solutions**, a software company selling enterprise products. The dashboard helps sales leadership:

- Track revenue performance vs. targets
- Identify top-performing sales reps and regions
- Understand customer segments and buying patterns
- Monitor deal pipeline health

## 📈 Key Metrics & KPIs

| Metric | Description |
|--------|-------------|
| Total Revenue | Sum of all closed-won deals |
| Average Deal Size | Mean revenue per closed deal |
| Win Rate | Closed-won / Total opportunities |
| Sales Cycle Length | Days from opportunity creation to close |
| Revenue by Segment | Breakdown by customer size (SMB/Mid-Market/Enterprise) |
| MoM Growth | Month-over-month revenue change |

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Data Storage** | SQLite / PostgreSQL |
| **ETL & Analysis** | Python (pandas, numpy) |
| **SQL Queries** | Raw SQL for aggregations |
| **Visualization** | Streamlit + Plotly |
| **Version Control** | Git |

## 📁 Project Structure

```
sales-dashboard/
├── README.md                 # You are here
├── INSTRUCTIONS.md           # How to customize & present
├── data/
│   ├── raw/
│   │   ├── sales_transactions.csv
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   └── sales_reps.csv
│   └── processed/            # Output from ETL
├── sql/
│   ├── schema.sql            # Database schema
│   ├── revenue_analysis.sql  # Revenue queries
│   ├── customer_segments.sql # Segmentation queries
│   └── sales_performance.sql # Rep performance queries
├── python/
│   ├── etl_pipeline.py       # Data loading & transformation
│   ├── analysis.py           # Analytical functions
│   ├── database.py           # DB connection utilities
│   └── dashboard.py          # Streamlit app
├── requirements.txt          # Python dependencies
└── docs/
    └── screenshots/          # Dashboard screenshots
```

## 🚀 Quick Start

### 1. Set Up Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run ETL Pipeline

```bash
# Load and transform data
python python/etl_pipeline.py
```

### 3. Launch Dashboard

```bash
# Start Streamlit app
streamlit run python/dashboard.py
```

Open http://localhost:8501 in your browser.

## 📊 Sample Insights

From analyzing this dataset, key findings include:

1. **Enterprise segment** generates 58% of revenue despite being only 12% of customers
2. **Q4** shows strongest performance due to end-of-year budget cycles
3. **Top 20% of reps** close 65% of total revenue
4. Average **sales cycle is 45 days** for Enterprise vs 18 days for SMB

## 🔍 SQL Query Examples

```sql
-- Monthly revenue trend with MoM growth
SELECT 
    DATE_TRUNC('month', close_date) as month,
    SUM(deal_value) as revenue,
    LAG(SUM(deal_value)) OVER (ORDER BY DATE_TRUNC('month', close_date)) as prev_month,
    ROUND(
        (SUM(deal_value) - LAG(SUM(deal_value)) OVER (ORDER BY DATE_TRUNC('month', close_date))) 
        / LAG(SUM(deal_value)) OVER (ORDER BY DATE_TRUNC('month', close_date)) * 100, 
        2
    ) as mom_growth_pct
FROM sales_transactions
WHERE status = 'Closed Won'
GROUP BY DATE_TRUNC('month', close_date)
ORDER BY month;
```

## 🎓 Skills Demonstrated

- **Data Engineering**: ETL pipeline design, data cleaning, normalization
- **SQL**: Complex queries with window functions, CTEs, aggregations
- **Python**: pandas data manipulation, modular code structure
- **Data Visualization**: Interactive charts, KPI cards, filters
- **Business Analysis**: Translating data into actionable insights

## 📝 Future Enhancements

- [ ] Add forecasting with Prophet or ARIMA
- [ ] Implement cohort analysis
- [ ] Add drill-down capabilities
- [ ] Connect to live CRM via API
- [ ] Deploy to cloud (Streamlit Cloud / AWS)

## 👤 Author

**Tommy Lu**  
Aspiring Data Analyst | [LinkedIn](#) | [GitHub](#)

---

*This is a portfolio project using synthetic data for demonstration purposes.*
