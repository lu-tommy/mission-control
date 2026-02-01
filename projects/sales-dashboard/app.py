import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = 'sales_dashboard.db'

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                product_id INTEGER,
                region TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                revenue REAL NOT NULL,
                cost REAL NOT NULL,
                profit REAL
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    return False

def generate_sample_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    products = [
        (1, 'Aerospace Cable', 'Components'),
        (2, 'Avionics Systems', 'Electronics'),
        (3, 'Defense Equipment', 'Hardware'),
        (4, 'Propulsion Systems', 'Systems'),
        (5, 'Navigation Equipment', 'Electronics')
    ]
    
    regions = ['Northeast', 'Southeast', 'Midwest', 'West', 'International']
    start_date = datetime(2025, 1, 1)
    
    for pid, name, category in products:
        c.execute('INSERT OR IGNORE INTO products (id, name, category) VALUES (?, ?, ?)', (pid, name, category))
    
    for i in range(100):
        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        pid = (i % len(products)) + 1
        region = regions[i % len(regions)]
        quantity = (i + 1) * 10
        revenue = quantity * (100 + i * 5)
        cost = revenue * (0.4 + (i % 3) * 0.1)
        profit = revenue - cost
        
        c.execute('''INSERT INTO sales (date, product_id, region, quantity, revenue, cost, profit) 
                      VALUES (?, ?, ?, ?, ?, ?)''', 
                 (date, pid, region, quantity, revenue, cost, profit))
    
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect(DB_PATH)
    
    sales = pd.read_sql_query('''
        SELECT s.date, p.name as product, s.region, s.quantity, s.revenue, s.cost, s.profit
        FROM sales s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.date DESC
        LIMIT 50
    ''', conn)
    
    conn.close()
    return sales

st.set_page_config(page_title='Sales Dashboard', layout='wide')

st.title('📊 Sales Dashboard')
st.markdown('''
    Interactive sales dashboard showcasing **Business Intelligence** skills.
    
    - **Data Visualization** with Plotly charts
    - **SQL Queries** for filtering and aggregation
    - **Aerospace Industry** themed sample data
    - **Date Range** filtering
    - **Export** to CSV
''')

col1, col2 = st.columns([1, 2])

date_range = st.date_input(
    'Date Range',
    [datetime(2025, 1, 1), datetime.now()],
    key='date_range'
)

sales_data = load_data()

if date_range:
    start_date, end_date = date_range
    sales_data = sales_data[
        (pd.to_datetime(sales_data['date']) >= start_date) & 
        (pd.to_datetime(sales_data['date']) <= end_date)
    ]

if sales_data.empty:
    st.warning('No sales data in selected range')
else:
    with col1:
        st.subheader('📊 Sales Metrics')
        
        total_revenue = sales_data['revenue'].sum()
        total_cost = sales_data['cost'].sum()
        total_profit = sales_data['profit'].sum()
        
        metric1, metric2, metric3, metric4 = st.columns(4)
        with metric1:
            st.metric('Total Revenue', f'${total_revenue:,.2f}', help_text='Sum of all sales revenue')
        with metric2:
            st.metric('Total Cost', f'${total_cost:,.2f}', help_text='Sum of all costs')
        with metric3:
            st.metric('Total Profit', f'${total_profit:,.2f}', delta_color='inverse', help_text='Revenue minus cost')
        with metric4:
            profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            st.metric('Profit Margin', f'{profit_margin:.1f}%', help_text='Profit as % of revenue')

    with col2:
        st.subheader('📈 Sales Trend')
        
        sales_data['date'] = pd.to_datetime(sales_data['date'])
        
        fig_trend = px.line(sales_data, x='date', y='revenue',
                             title='Revenue Trend',
                             labels={'value':'Revenue'},
                             template='simple')
        st.plotly_chart(fig_trend, use_container_width=True)
        
        fig_profit = px.bar(sales_data, x='date', y='profit',
                             title='Daily Profit',
                             labels={'value':'Profit'},
                             color='profit' if profit_margin > 0 else 'cost')
        st.plotly_chart(fig_profit, use_container_width=True)

    st.divider()

    with col1:
        st.subheader('📋 Data Table')
        
        display_cols = ['date', 'product', 'region', 'quantity', 'revenue', 'cost', 'profit']
        sales_data_display = sales_data[display_cols].sort_values('date', ascending=False)
        
        st.dataframe(sales_data_display, use_container_width=True, height=300)

st.divider()

with col1:
    st.subheader('⚙️ Controls')

    c1, c2 = st.columns([1, 1])
    
    with c1:
        if st.button('🔄 Refresh Data', use_container_width=True):
            sales_data = load_data()
            st.rerun()
        
        if st.button('📥 Generate New Sample', use_container_width=True):
            init_db()
            generate_sample_data()
            st.success('Sample data generated!')
            st.rerun()
        
        if st.button('📊 Reset Dashboard', use_container_width=True):
            st.rerun()
    
    with c2:
        if st.button('📥 Export to CSV', use_container_width=True):
            if not sales_data.empty:
                csv = sales_data.to_csv(index=False)
                st.download_button('Download Sales Data', csv, 'text/csv')
            else:
                st.warning('No data to export')

with col1:
    st.subheader('ℹ️ About')
    st.markdown('''
        - **Total Records**: `{len(sales_data)}` sales
        - **Date Range**: Showing selected date range
        - **Database**: SQLite (`sales_dashboard.db`)
        - **Built with**: Python, Streamlit, Plotly, SQLite
    ''')

# Initialize DB on first run
if not os.path.exists(DB_PATH):
    with st.spinner('Initializing database...'):
        init_db()
        generate_sample_data()
    st.success('Dashboard initialized with sample data!')
