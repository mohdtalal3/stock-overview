import streamlit as st
import subprocess
import time
import threading
from queue import Queue
from stock_spider import run_spider
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(page_title="Product Stock Management", layout="wide")

def run_scraper():
    message_queue = Queue()
    
    def scraper_thread():
        run_spider(message_queue)
    
    thread = threading.Thread(target=scraper_thread)
    thread.start()
    
    placeholder = st.empty()
    log_messages = []
    with st.spinner("Scraping in progress..."):
        while thread.is_alive() or not message_queue.empty():
            try:
                message = message_queue.get(timeout=0.1)
                log_messages.append(message)
                placeholder.text("\n".join(log_messages))
            except:
                pass
    
        st.success("Scraping completed successfully!")

def get_connection():
    return sqlite3.connect('product_database.db', check_same_thread=False)

def load_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if the required tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='product_info' OR name='stock_data')")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    if 'product_info' not in existing_tables or 'stock_data' not in existing_tables:
        # If tables don't exist, return an empty DataFrame
        return pd.DataFrame()
    
    # If tables exist, proceed with the query
    query = """
    SELECT pi.category, pi.subcategory, pi.product_name, sd.price, sd.date, sd.stock_amount
    FROM product_info pi
    JOIN stock_data sd ON pi.id = sd.product_id
    """
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

def main():
    menu = ["Product Overview", "Run Scraper", "Stock Tracker"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Product Overview":
        st.title("Product Stock Management System")
        st.write("Welcome to the Product Stock Management System!")
        
        # Load data
        df = load_data()
        
        if df.empty:
            st.warning("No data available. The database might be empty or not initialized. Please run the scraper to collect data.")
        else:
            # Date range selector
            st.sidebar.header("Date Range")
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()
            
            # Set default date range to last 30 days, but not exceeding available data range
            default_end_date = max_date
            default_start_date = max(min_date, default_end_date - timedelta(days=30))

            start_date = st.sidebar.date_input("Start Date", default_start_date, min_value=min_date, max_value=max_date)
            end_date = st.sidebar.date_input("End Date", default_end_date, min_value=start_date, max_value=max_date)
            
            # Ensure end_date is not before start_date
            if start_date > end_date:
                st.sidebar.error('Error: End date must fall after start date.')
            else:
                # Filter data based on date range
                mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
                filtered_df = df.loc[mask]
                
                if filtered_df.empty:
                    st.warning("No data available for the selected date range.")
                else:
                    # Calculate stock changes and price changes
                    stock_changes = filtered_df.groupby('product_name').agg({
                        'stock_amount': ['first', 'last'],
                        'price': ['first', 'last']
                    })
                    stock_changes.columns = ['initial_stock', 'final_stock', 'initial_price', 'current_price']
                    stock_changes['stock_change'] = stock_changes['final_stock'] - stock_changes['initial_stock']
                    stock_changes['stock_change_percentage'] = (stock_changes['stock_change'] / stock_changes['initial_stock']) * 100
                    stock_changes['price_change'] = stock_changes['current_price'] - stock_changes['initial_price']
                    stock_changes['price_change_percentage'] = (stock_changes['price_change'] / stock_changes['initial_price']) * 100
                    
                    # Remove rows with null stock amounts
                    stock_changes = stock_changes.dropna(subset=['initial_stock', 'final_stock', 'initial_price', 'current_price'])
                    
                    # Sort by absolute stock change percentage
                    stock_changes = stock_changes.sort_values('stock_change_percentage', key=abs, ascending=False)
                    
                    # Display overview
                    st.subheader(f"Product Stock and Price Overview ({start_date} to {end_date})")
                    
                    # Prepare data for display
                    display_df = stock_changes.reset_index()
                    display_df['stock_change_percentage'] = display_df['stock_change_percentage'].round(2)
                    display_df['price_change_percentage'] = display_df['price_change_percentage'].round(2)
                    
                    # Format numeric columns
                    for col in ['initial_stock', 'final_stock', 'stock_change']:
                        display_df[col] = display_df[col].astype(int)
                    for col in ['initial_price', 'current_price', 'price_change']:
                        display_df[col] = display_df[col].round(2)

                    gb = GridOptionsBuilder.from_dataframe(display_df)
                    gb.configure_pagination(paginationAutoPageSize=True)
                    gb.configure_side_bar()
                    gb.configure_selection('single', use_checkbox=True, groupSelectsChildren="Group checkbox select children")
                    gb.configure_columns(['initial_stock', 'final_stock', 'stock_change'], type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=0)
                    gb.configure_column("stock_change_percentage", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=2, valueFormatter="data.stock_change_percentage.toFixed(2) + '%'")
                    gb.configure_column("price_change_percentage", type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=2, valueFormatter="data.price_change_percentage.toFixed(2) + '%'")
                    for col in ['initial_price', 'current_price', 'price_change']:
                        gb.configure_column(col, type=["numericColumn", "numberColumnFilter", "customNumericFormat"], precision=2, valueFormatter=f"'$' + data.{col}.toFixed(2)")
                    gridOptions = gb.build()

                    AgGrid(display_df, gridOptions=gridOptions, enable_enterprise_modules=True, 
                            update_mode='MODEL_CHANGED', height=800, fit_columns_on_grid_load=False)

    elif choice == "Run Scraper":
        st.subheader("Web Scraper")
        if st.button("Start Scraping"):
            run_scraper()

    elif choice == "Stock Tracker":
        import stock_tracker
        stock_tracker.main()

if __name__ == "__main__":
    main()