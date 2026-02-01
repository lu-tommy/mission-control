# Sales Dashboard

Interactive sales dashboard showcasing BI skills.

## Tech Stack
- Python (pandas, plotly)
- SQL (SQLite)
- Dashboard: Streamlit

## Features
- Sales metrics (revenue, orders, customers)
- Product performance analysis
- Regional comparison
- Date range filtering
- Export to CSV

## Setup
\`\`\`bash
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Data Schema
\`\`\`sql
CREATE TABLE sales (
  id INTEGER PRIMARY KEY,
  date TEXT NOT NULL,
  product_id INTEGER,
  region TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  revenue REAL NOT NULL,
  cost REAL NOT NULL,
  profit REAL
);

CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT
);
\`\`\`
