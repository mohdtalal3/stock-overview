import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Connect to the SQLite database
@st.cache_resource
def get_connection():
    return sqlite3.connect('product_database.db', check_same_thread=False)

conn = get_connection()

# Function to load data from the database
@st.cache_data
def load_data():
    query = """
    SELECT pi.category, pi.subcategory, pi.product_name, sd.date, sd.stock_amount
    FROM product_info pi
    JOIN stock_data sd ON pi.id = sd.product_id
    """
    df = pd.read_sql_query(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

# Load the data
df = load_data()

# Streamlit app
st.title('Product Stock Tracker')

# Sidebar filters
st.sidebar.header('Filters')

# Category filter
categories = sorted(df['category'].unique().tolist())
selected_category = st.sidebar.selectbox('Select Category', categories)

# Subcategory filter (dependent on category)
subcategories = sorted(df[df['category'] == selected_category]['subcategory'].unique().tolist())
selected_subcategory = st.sidebar.selectbox('Select Subcategory', subcategories)

# Product name filter (dependent on category and subcategory)
products = sorted(df[(df['category'] == selected_category) & 
                     (df['subcategory'] == selected_subcategory)]['product_name'].unique().tolist())
selected_product = st.sidebar.selectbox('Select Product', products)

# Date range filter
min_date = df['date'].min().date()
max_date = df['date'].max().date()

# Ensure the default dates are within the available range
default_start_date = max(min_date, max_date - timedelta(days=30))
default_end_date = max_date

start_date = st.sidebar.date_input('Start Date', default_start_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input('End Date', default_end_date, min_value=min_date, max_value=max_date)

# Ensure end_date is not before start_date
if start_date > end_date:
    st.sidebar.error('Error: End date must fall after start date.')
    st.stop()

# Filter the dataframe based on selections
filtered_df = df[(df['category'] == selected_category) & 
                 (df['subcategory'] == selected_subcategory) & 
                 (df['product_name'] == selected_product) & 
                 (df['date'].dt.date >= start_date) & 
                 (df['date'].dt.date <= end_date)]

# Sort the dataframe by date
filtered_df = filtered_df.sort_values('date')

# Calculate the stock difference
filtered_df['stock_difference'] = filtered_df['stock_amount'].diff().fillna(0).astype(int)

# Function to format stock difference
def format_stock_difference(value):
    value = int(value)  # Convert to standard Python int
    if value > 0:
        return f"+{value} 📈"
    elif value < 0:
        return f"{value} 📉"
    else:
        return "0"

# Display the stock price chart
if not filtered_df.empty:
    st.subheader(f'Stock Amounts Over Time for {selected_product}')
    
    fig = px.bar(filtered_df, x='date', y='stock_amount',
                 title=f'Product Stock Over Time - {selected_product}',
                 labels={'date': 'Date', 'stock_amount': 'Stock Amount'})
    
    fig.update_layout(xaxis_title="Date", yaxis_title="Stock Amount")
    st.plotly_chart(fig)

    # Display the data table with stock difference
    st.subheader('Stock Data')
    display_df = filtered_df[['date', 'stock_amount', 'stock_difference']].copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['stock_change'] = display_df['stock_difference'].apply(format_stock_difference)
    
    st.dataframe(display_df[['date', 'stock_amount', 'stock_change']], width=800)

    # Display current stock and change from previous record
    if len(filtered_df) > 1:
        current_stock = int(filtered_df['stock_amount'].iloc[-1])
        previous_stock = int(filtered_df['stock_amount'].iloc[-2])
        stock_change = int(current_stock - previous_stock)
        
        st.subheader("Current Stock Information")
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Stock", current_stock)
        col2.metric("Previous Stock", previous_stock)
        col3.metric("Stock Change", stock_change, delta=stock_change)

else:
    st.warning('No data available for the selected filters.')

# Close the database connection
conn.close()