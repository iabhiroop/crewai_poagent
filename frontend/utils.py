"""
Utility functions for the AI Purchase Order System Frontend
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

def format_currency(amount, currency="USD"):
    """Format currency values consistently"""
    return f"${amount:,.2f}" if currency == "USD" else f"{amount:,.2f} {currency}"

def format_date(date_string):
    """Format date strings consistently"""
    try:
        if isinstance(date_string, str):
            date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date_obj.strftime('%Y-%m-%d %H:%M')
        return str(date_string)
    except:
        return str(date_string)

def get_status_color(status):
    """Get color for status indicators"""
    colors = {
        "Critical": "#dc3545",
        "Low": "#ffc107", 
        "Medium": "#fd7e14",
        "Good": "#28a745",
        "Pending": "#17a2b8",
        "Completed": "#28a745",
        "Error": "#dc3545"
    }
    return colors.get(status, "#6c757d")

def create_metric_card(title, value, delta=None, delta_color="normal"):
    """Create a styled metric card"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(title, value, delta=delta, delta_color=delta_color)

def safe_json_loads(json_string):
    """Safely load JSON with error handling"""
    try:
        if isinstance(json_string, str):
            return json.loads(json_string)
        return json_string
    except (json.JSONDecodeError, TypeError):
        return {}

def calculate_inventory_health(df):
    """Calculate overall inventory health score"""
    if df.empty:
        return 0
    
    total_items = len(df)
    critical_items = len(df[df['status'] == 'Critical'])
    low_items = len(df[df['status'] == 'Low'])
    
    # Health score calculation (0-100)
    critical_penalty = critical_items * 20
    low_penalty = low_items * 10
    
    health_score = max(0, 100 - critical_penalty - low_penalty)
    return health_score

def create_status_chart(df, column="status"):
    """Create a standardized status distribution chart"""
    if df.empty:
        return None
        
    status_counts = df[column].value_counts()
    colors = [get_status_color(status) for status in status_counts.index]
    
    fig = px.pie(
        values=status_counts.values, 
        names=status_counts.index,
        color_discrete_sequence=colors,
        title=f"{column.title()} Distribution"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_value_chart(df, x_col, y_col, title="Value Distribution"):
    """Create a standardized value chart"""
    if df.empty:
        return None
        
    fig = px.bar(
        df, 
        x=x_col, 
        y=y_col,
        title=title,
        color=y_col,
        color_continuous_scale="blues"
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def filter_dataframe(df, filters):
    """Apply multiple filters to a dataframe"""
    filtered_df = df.copy()
    
    for column, value in filters.items():
        if value and value != "All" and column in df.columns:
            filtered_df = filtered_df[filtered_df[column] == value]
    
    return filtered_df

def get_system_status():
    """Check system component status"""
    status = {
        "sqlite": False,
        "mongodb": False,
        "queue_file": False,
        "inventory_db": False,
        "email_config": False
    }
    
    # Check SQLite
    try:
        import sqlite3
        conn = sqlite3.connect("inventory.db")
        conn.close()
        status["sqlite"] = True
        status["inventory_db"] = True
    except:
        pass
    
    # Check MongoDB
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
        client.admin.command('ismaster')
        client.close()
        status["mongodb"] = True
    except:
        pass
    
    # Check queue file
    status["queue_file"] = os.path.exists("purchase_queue.json")
    
    # Check email config
    status["email_config"] = bool(os.getenv('supemail'))
    
    return status

def display_system_status():
    """Display system status indicators"""
    status = get_system_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Database Status:**")
        st.write(f"{'✅' if status['sqlite'] else '❌'} SQLite (Inventory)")
        st.write(f"{'✅' if status['mongodb'] else '❌'} MongoDB (Orders)")
    
    with col2:
        st.write("**File System:**")
        st.write(f"{'✅' if status['queue_file'] else '❌'} Purchase Queue")
        st.write(f"{'✅' if status['inventory_db'] else '❌'} Inventory DB")
    
    with col3:
        st.write("**Configuration:**")
        st.write(f"{'✅' if status['email_config'] else '⚠️'} Email Config")

def create_timeline_chart(data, date_col, value_col, title="Timeline"):
    """Create a timeline chart"""
    if not data:
        return None
        
    df = pd.DataFrame(data)
    if df.empty or date_col not in df.columns:
        return None
        
    df[date_col] = pd.to_datetime(df[date_col])
    
    fig = px.line(
        df, 
        x=date_col, 
        y=value_col,
        title=title,
        markers=True
    )
    fig.update_layout(xaxis_title="Date", yaxis_title=value_col.title())
    return fig

def show_loading_spinner(message="Processing..."):
    """Show a loading spinner with message"""
    return st.spinner(message)

def show_success_message(message):
    """Show success message with consistent styling"""
    st.success(f"✅ {message}")

def show_error_message(message):
    """Show error message with consistent styling"""
    st.error(f"❌ {message}")

def show_warning_message(message):
    """Show warning message with consistent styling"""
    st.warning(f"⚠️ {message}")

def show_info_message(message):
    """Show info message with consistent styling"""
    st.info(f"ℹ️ {message}")

def create_download_button(data, filename, label="Download Data"):
    """Create a download button for data"""
    if isinstance(data, pd.DataFrame):
        csv = data.to_csv(index=False)
        return st.download_button(
            label=label,
            data=csv,
            file_name=filename,
            mime='text/csv'
        )
    elif isinstance(data, (dict, list)):
        json_data = json.dumps(data, indent=2)
        return st.download_button(
            label=label,
            data=json_data,
            file_name=filename,
            mime='application/json'
        )
    return None

def paginate_dataframe(df, page_size=20):
    """Add pagination to dataframes"""
    if df.empty:
        return df
        
    total_pages = len(df) // page_size + (1 if len(df) % page_size > 0 else 0)
    
    if total_pages > 1:
        page = st.selectbox("Page", range(1, total_pages + 1))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return df.iloc[start_idx:end_idx]
    
    return df
