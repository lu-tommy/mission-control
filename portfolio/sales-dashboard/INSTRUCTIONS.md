# 📋 Instructions: How to Use & Present This Project

This guide helps you customize, run, and present the Sales Performance Dashboard as a portfolio project.

---

## 🚀 Quick Start

### 1. Set Up Your Environment

```bash
# Navigate to project
cd portfolio/sales-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the ETL Pipeline

```bash
python python/etl_pipeline.py
```

This creates `data/sales_dashboard.db` with all the sample data loaded.

### 3. Launch the Dashboard

```bash
streamlit run python/dashboard.py
```

Open http://localhost:8501 to see your dashboard!

---

## 🎨 Customization Options

### Change Company Name/Branding

Edit `python/dashboard.py`:
- Change "TechFlow Solutions" to your preferred company name
- Update colors in the `st.markdown()` CSS section
- Modify the sidebar "About" text

### Modify the Sample Data

The CSV files in `data/raw/` are easily editable:

**customers.csv:**
- Add more companies in different industries
- Adjust company sizes and revenue
- Change regions/states

**products.csv:**
- Rename products to match a different industry
- Adjust pricing tiers
- Add more products

**sales_reps.csv:**
- Change names, regions, quotas
- Add or remove team members

**sales_transactions.csv:**
- Add more deals
- Adjust date ranges
- Modify deal values

After editing CSVs, re-run `python etl_pipeline.py` to rebuild the database.

### Add New Metrics

1. Add SQL query in `sql/` folder
2. Create function in `python/analysis.py`
3. Add visualization in `python/dashboard.py`

Example: Adding "Average Discount" metric:

```python
# In analysis.py
def get_avg_discount():
    query = """
        SELECT AVG(discount_pct) * 100 as avg_discount
        FROM sales_transactions
        WHERE status = 'Closed Won'
    """
    return execute_query(query)['avg_discount'].iloc[0]

# In dashboard.py - add to KPI row
st.metric("Avg Discount", f"{get_avg_discount():.1f}%")
```

---

## 🎤 How to Present This Project

### In an Interview

**Opening (30 seconds):**
> "I built a sales performance dashboard to demonstrate my data analytics skills. It processes B2B sales data through a Python ETL pipeline, stores it in a SQL database, and visualizes insights with an interactive Streamlit dashboard."

**Key Talking Points:**

1. **ETL Pipeline**
   - "The pipeline extracts from CSV, transforms with pandas, and loads to SQLite"
   - "I included data validation and error handling"
   - "It's modular - easy to swap in PostgreSQL or add new data sources"

2. **SQL Skills**
   - "I wrote complex queries with CTEs, window functions, and aggregations"
   - "The schema includes proper foreign keys and indexes for performance"
   - "I created views for common analysis patterns"

3. **Data Analysis**
   - Point out specific insights: "Enterprise customers generate 58% of revenue"
   - Show the segment × product matrix
   - Discuss win rate analysis

4. **Visualization**
   - Walk through the dashboard pages
   - Highlight interactivity (filters, drill-downs)
   - Explain design choices (why donut chart for segments, etc.)

**Handle These Questions:**

Q: "What was the most challenging part?"
> "Designing the ETL to be extensible. I wanted future-me (or a team) to easily add new data sources without rewriting everything."

Q: "How would you improve this?"
> "I'd add forecasting with Prophet, deploy to Streamlit Cloud, and connect to a real CRM API instead of static CSVs."

Q: "Why SQLite instead of PostgreSQL?"
> "For portfolio portability - no server setup required. But the code uses SQLAlchemy, so switching databases is just changing the connection string."

### On GitHub/Portfolio Site

Add these to your README:
- Screenshot of the dashboard (use Streamlit's screenshot feature)
- Link to live demo (deploy to Streamlit Cloud - it's free!)
- Clear "How to Run" instructions

Update the Author section with your actual links:
```markdown
## 👤 Author

**Your Name**  
[LinkedIn](your-linkedin-url) | [GitHub](your-github-url) | [Portfolio](your-site)
```

---

## 📸 Taking Screenshots

1. Run the dashboard: `streamlit run python/dashboard.py`
2. Navigate to each page
3. Use browser screenshot or Snipping Tool
4. Save to `docs/screenshots/`

Recommended screenshots:
- `dashboard-preview.png` - Executive Summary (main image)
- `revenue-analysis.png` - Revenue trends
- `sales-team.png` - Rep leaderboard
- `pipeline.png` - Pipeline funnel

---

## 🌐 Deploying to Streamlit Cloud (Free!)

1. Push your project to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select your repo, branch, and `python/dashboard.py`
6. Click "Deploy"

Your live URL will be: `https://your-username-your-repo.streamlit.app`

### Before Deploying

Make sure `requirements.txt` is at project root or update Streamlit Cloud settings to point to it.

---

##