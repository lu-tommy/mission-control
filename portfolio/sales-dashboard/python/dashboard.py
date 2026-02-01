"""
Sales Performance Dashboard
Author: Tommy Lu

Interactive dashboard built with Streamlit and Plotly.

Run with:
    streamlit run dashboard.py

The dashboard shows:
1. Executive Summary (KPIs)
2. Revenue Trends
3. Segment Analysis
4. Sales Rep Performance
5. Pipeline Health
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from analysis import (
    get_revenue_kpis,
    get_monthly_revenue,
    get_revenue_by_segment,
    get_revenue_by_product,
    get_revenue_by_region,
    get_rep_leaderboard,
    get_rep_monthly_trend,
    get_top_customers,
    get_customer_segments_analysis,
    get_pipeline_summary,
    get_total_pipeline_value,
    get_date_range
)


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Sales Performance Dashboard",
    page_icon="📊",
    layout="wide",  # Use full width
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.title("🎛️ Dashboard Controls")
    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "Navigate to:",
        ["📈 Executive Summary", "💰 Revenue Analysis", "👥 Sales Team", "🏢 Customers", "📊 Pipeline"]
    )
    
    st.markdown("---")
    
    # About section
    st.markdown("### About")
    st.markdown("""
    This dashboard analyzes sales performance for **TechFlow Solutions**, 
    tracking revenue, customer segments, and sales team metrics.
    
    **Data Range:**
    """)
    
    try:
        min_date, max_date = get_date_range()
        st.write(f"📅 {min_date} to {max_date}")
    except:
        st.write("Run ETL pipeline first")
    
    st.markdown("---")
    st.markdown("*Built with Streamlit + Plotly*")
    st.markdown("*Author: Tommy Lu*")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_currency(value):
    """Format number as currency string."""
    return f"${value:,.0f}"


def format_percent(value):
    """Format number as percentage string."""
    return f"{value:.1f}%"


def create_kpi_card(label, value, delta=None):
    """Create a KPI metric display."""
    st.metric(label=label, value=value, delta=delta)


# =============================================================================
# PAGE: EXECUTIVE SUMMARY
# =============================================================================

def render_executive_summary():
    """Render the executive summary page with key KPIs."""
    
    st.title("📈 Executive Summary")
    st.markdown("High-level overview of sales performance")
    st.markdown("---")
    
    # Get KPIs
    try:
        kpis = get_revenue_kpis()
        pipeline_value = get_total_pipeline_value()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure to run the ETL pipeline first: `python etl_pipeline.py`")
        return
    
    # KPI Cards Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Revenue",
            value=format_currency(kpis['total_revenue']),
            delta="vs target"  # Placeholder
        )
    
    with col2:
        st.metric(
            label="Deals Won",
            value=kpis['deal_count'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="Avg Deal Size",
            value=format_currency(kpis['avg_deal_size']),
            delta=None
        )
    
    with col4:
        st.metric(
            label="Win Rate",
            value=format_percent(kpis['win_rate']),
            delta=None
        )
    
    st.markdown("---")
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Revenue Trend")
        
        monthly_df = get_monthly_revenue()
        
        fig = px.line(
            monthly_df,
            x='month_date',
            y='revenue',
            markers=True,
            labels={'month_date': 'Month', 'revenue': 'Revenue ($)'}
        )
        fig.update_layout(
            hovermode='x unified',
            yaxis_tickformat='$,.0f'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Revenue by Segment")
        
        segment_df = get_revenue_by_segment()
        
        fig = px.pie(
            segment_df,
            values='revenue',
            names='segment',
            hole=0.4,  # Donut chart
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    # Pipeline snapshot
    st.markdown("---")
    st.subheader("📊 Pipeline Snapshot")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.metric(
            label="Pipeline Value",
            value=format_currency(pipeline_value)
        )
    
    with col2:
        pipeline_df = get_pipeline_summary()
        
        fig = px.bar(
            pipeline_df,
            x='stage',
            y='pipeline_value',
            color='stage',
            text='opportunity_count',
            labels={'pipeline_value': 'Value ($)', 'stage': 'Stage'}
        )
        fig.update_traces(texttemplate='%{text} deals', textposition='outside')
        fig.update_layout(showlegend=False, yaxis_tickformat='$,.0f')
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGE: REVENUE ANALYSIS
# =============================================================================

def render_revenue_analysis():
    """Render detailed revenue analysis page."""
    
    st.title("💰 Revenue Analysis")
    st.markdown("Deep dive into revenue metrics and trends")
    st.markdown("---")
    
    # Monthly trend with MoM growth
    st.subheader("Monthly Revenue with MoM Growth")
    
    monthly_df = get_monthly_revenue()
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Revenue bars
    fig.add_trace(
        go.Bar(
            x=monthly_df['month'],
            y=monthly_df['revenue'],
            name="Revenue",
            marker_color='steelblue'
        ),
        secondary_y=False
    )
    
    # MoM growth line
    fig.add_trace(
        go.Scatter(
            x=monthly_df['month'],
            y=monthly_df['mom_growth_pct'],
            name="MoM Growth %",
            line=dict(color='orange', width=2),
            mode='lines+markers'
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    fig.update_yaxes(title_text="Revenue ($)", tickformat='$,.0f', secondary_y=False)
    fig.update_yaxes(title_text="MoM Growth (%)", tickformat='.1f', secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Product and Region breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Revenue by Product")
        
        product_df = get_revenue_by_product()
        
        fig = px.bar(
            product_df,
            x='revenue',
            y='product_name',
            orientation='h',
            color='category',
            labels={'revenue': 'Revenue ($)', 'product_name': 'Product'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Revenue by Region")
        
        region_df = get_revenue_by_region()
        
        fig = px.bar(
            region_df,
            x='revenue',
            y='region',
            orientation='h',
            color='revenue',
            color_continuous_scale='Blues',
            labels={'revenue': 'Revenue ($)', 'region': 'Region'}
        )
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.markdown("---")
    st.subheader("📋 Monthly Data Table")
    st.dataframe(
        monthly_df[['month', 'revenue', 'mom_growth_pct']].rename(columns={
            'month': 'Month',
            'revenue': 'Revenue ($)',
            'mom_growth_pct': 'MoM Growth (%)'
        }),
        use_container_width=True
    )


# =============================================================================
# PAGE: SALES TEAM
# =============================================================================

def render_sales_team():
    """Render sales team performance page."""
    
    st.title("👥 Sales Team Performance")
    st.markdown("Individual rep metrics and rankings")
    st.markdown("---")
    
    # Leaderboard
    st.subheader("🏆 Sales Leaderboard")
    
    rep_df = get_rep_leaderboard()
    
    # Format the dataframe for display
    display_df = rep_df.copy()
    display_df['total_revenue'] = display_df['total_revenue'].apply(lambda x: f"${x:,.0f}")
    display_df['avg_deal_size'] = display_df['avg_deal_size'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    display_df['win_rate_pct'] = display_df['win_rate_pct'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    display_df['quota_attainment_pct'] = display_df['quota_attainment_pct'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    
    st.dataframe(
        display_df[['rep_name', 'region', 'deals_won', 'total_revenue', 'avg_deal_size', 'win_rate_pct', 'quota_attainment_pct']].rename(columns={
            'rep_name': 'Rep Name',
            'region': 'Region',
            'deals_won': 'Deals Won',
            'total_revenue': 'Revenue',
            'avg_deal_size': 'Avg Deal',
            'win_rate_pct': 'Win Rate',
            'quota_attainment_pct': 'Quota %'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Revenue by Rep")
        
        fig = px.bar(
            rep_df.sort_values('total_revenue', ascending=True),
            x='total_revenue',
            y='rep_name',
            orientation='h',
            color='region',
            labels={'total_revenue': 'Revenue ($)', 'rep_name': 'Sales Rep'}
        )
        fig.update_layout(xaxis_tickformat='$,.0f')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Quota Attainment")
        
        fig = px.bar(
            rep_df.sort_values('quota_attainment_pct', ascending=True),
            x='quota_attainment_pct',
            y='rep_name',
            orientation='h',
            color='quota_attainment_pct',
            color_continuous_scale='RdYlGn',
            labels={'quota_attainment_pct': 'Quota Attainment (%)', 'rep_name': 'Sales Rep'}
        )
        # Add 100% target line
        fig.add_vline(x=100, line_dash="dash", line_color="gray", annotation_text="Target")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Rep trend over time
    st.markdown("---")
    st.subheader("📈 Rep Performance Trend")
    
    selected_reps = st.multiselect(
        "Select reps to compare:",
        options=rep_df['rep_name'].tolist(),
        default=rep_df['rep_name'].tolist()[:3]
    )
    
    if selected_reps:
        trend_df = get_rep_monthly_trend()
        trend_df = trend_df[trend_df['rep_name'].isin(selected_reps)]
        
        fig = px.line(
            trend_df,
            x='month',
            y='revenue',
            color='rep_name',
            markers=True,
            labels={'month': 'Month', 'revenue': 'Revenue ($)', 'rep_name': 'Rep'}
        )
        fig.update_layout(yaxis_tickformat='$,.0f')
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGE: CUSTOMERS
# =============================================================================

def render_customers():
    """Render customer analysis page."""
    
    st.title("🏢 Customer Analysis")
    st.markdown("Customer segments and top accounts")
    st.markdown("---")
    
    # Segment analysis
    st.subheader("Segment Analysis")
    
    segment_df = get_customer_segments_analysis()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Segment metrics table
        display_df = segment_df.copy()
        display_df['total_revenue'] = display_df['total_revenue'].apply(lambda x: f"${x:,.0f}")
        display_df['avg_deal_size'] = display_df['avg_deal_size'].apply(lambda x: f"${x:,.0f}")
        display_df['avg_sales_cycle_days'] = display_df['avg_sales_cycle_days'].apply(lambda x: f"{x:.0f} days")
        
        st.dataframe(
            display_df.rename(columns={
                'segment': 'Segment',
                'customer_count': 'Customers',
                'total_deals': 'Deals',
                'total_revenue': 'Revenue',
                'avg_deal_size': 'Avg Deal',
                'avg_sales_cycle_days': 'Sales Cycle'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    with col2:
        # Segment comparison chart
        fig = px.bar(
            segment_df,
            x='segment',
            y=['total_revenue', 'avg_deal_size'],
            barmode='group',
            labels={'value': 'Amount ($)', 'segment': 'Segment'}
        )
        fig.update_layout(yaxis_tickformat='$,.0f')
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Top customers
    st.subheader("🌟 Top Customers by Lifetime Value")
    
    top_n = st.slider("Number of customers to show:", 5, 20, 10)
    
    top_customers = get_top_customers(limit=top_n)
    
    fig = px.bar(
        top_customers.sort_values('lifetime_value', ascending=True),
        x='lifetime_value',
        y='company_name',
        orientation='h',
        color='segment',
        hover_data=['industry', 'total_purchases'],
        labels={'lifetime_value': 'Lifetime Value ($)', 'company_name': 'Company'}
    )
    fig.update_layout(xaxis_tickformat='$,.0f', height=400)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# PAGE: PIPELINE
# =============================================================================

def render_pipeline():
    """Render pipeline analysis page."""
    
    st.title("📊 Pipeline Analysis")
    st.markdown("Current opportunities and forecast")
    st.markdown("---")
    
    # Pipeline summary
    pipeline_df = get_pipeline_summary()
    total_pipeline = get_total_pipeline_value()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Pipeline Value", format_currency(total_pipeline))
    
    with col2:
        total_opps = pipeline_df['opportunity_count'].sum()
        st.metric("Total Opportunities", int(total_opps))
    
    with col3:
        avg_opp = total_pipeline / total_opps if total_opps > 0 else 0
        st.metric("Avg Opportunity Size", format_currency(avg_opp))
    
    st.markdown("---")
    
    # Pipeline funnel
    st.subheader("Pipeline Funnel")
    
    # Order stages properly for funnel
    stage_order = ['Discovery', 'Qualification', 'Proposal', 'Negotiation']
    pipeline_df['stage'] = pd.Categorical(pipeline_df['stage'], categories=stage_order, ordered=True)
    pipeline_df = pipeline_df.sort_values('stage')
    
    fig = px.funnel(
        pipeline_df,
        x='pipeline_value',
        y='stage',
        color='stage'
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Pipeline table
    st.markdown("---")
    st.subheader("📋 Pipeline by Stage")
    
    display_df = pipeline_df.copy()
    display_df['pipeline_value'] = display_df['pipeline_value'].apply(lambda x: f"${x:,.0f}")
    display_df['avg_opp_size'] = display_df['avg_opp_size'].apply(lambda x: f"${x:,.0f}")
    
    st.dataframe(
        display_df.rename(columns={
            'stage': 'Stage',
            'opportunity_count': 'Opportunities',
            'pipeline_value': 'Value',
            'avg_opp_size': 'Avg Size'
        }),
        use_container_width=True,
        hide_index=True
    )


# =============================================================================
# MAIN ROUTER
# =============================================================================

def main():
    """Main function - routes to selected page."""
    
    if page == "📈 Executive Summary":
        render_executive_summary()
    elif page == "💰 Revenue Analysis":
        render_revenue_analysis()
    elif page == "👥 Sales Team":
        render_sales_team()
    elif page == "🏢 Customers":
        render_customers()
    elif page == "📊 Pipeline":
        render_pipeline()


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    main()
