import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from PIL import Image
import io

# Connect to the SQLite database
def get_connection():
    return sqlite3.connect('product_database.db', check_same_thread=False)

conn = get_connection()

# Function to load data from the database
def load_data():
    query = """
    SELECT pi.category, pi.subcategory, pi.product_name, sd.price, sd.date, sd.stock_amount, sd.id as stock_id
    FROM product_info pi
    JOIN stock_data sd ON pi.id = sd.product_id
    """
    df = pd.read_sql_query(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

# Function to get screenshot from the database
def get_screenshot(stock_id):
    stock_id = int(stock_id)
    cursor = conn.cursor()
    cursor.execute("SELECT screenshot FROM stock_data WHERE id = ?", (stock_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None

# Function to format stock difference
def format_stock_difference(value):
    value = int(value)
    if value > 0:
        return f"+{value} 📈"
    elif value < 0:
        return f"{value} 📉"
    else:
        return "0"

def main():
    # Load the data
    df = load_data()

    st.title('Product Stock Tracker')

    # Sidebar filters
    st.sidebar.header('Filters')

    # Sort categories by maximum stock amount, descending
    category_stock = df.groupby('category')['stock_amount'].max().sort_values(ascending=False)
    categories = category_stock.index.tolist()
    selected_category = st.sidebar.selectbox('Select Category', categories)

    # Filter and sort subcategories
    subcategory_df = df[df['category'] == selected_category]
    subcategory_stock = subcategory_df.groupby('subcategory')['stock_amount'].max().sort_values(ascending=False)
    subcategories = subcategory_stock.index.tolist()
    selected_subcategory = st.sidebar.selectbox('Select Subcategory', subcategories)

    # Filter and sort products
    product_df = subcategory_df[subcategory_df['subcategory'] == selected_subcategory]
    product_stock = product_df.groupby('product_name')['stock_amount'].max().sort_values(ascending=False)
    products = product_stock.index.tolist()
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

    # Display the stock price chart
    if not filtered_df.empty:
        current_price = filtered_df['price'].iloc[-1]
        st.subheader(f'Stock Amounts Over Time for {selected_product} (Current Price: ${current_price:.2f})')
        
        fig = px.bar(filtered_df, x='date', y='stock_amount',
                     title=f'Product Stock Over Time - {selected_product}',
                     labels={'date': 'Date', 'stock_amount': 'Stock Amount'})
        
        fig.update_layout(xaxis_title="Date", yaxis_title="Stock Amount")
        st.plotly_chart(fig)

        # Display the price chart
        st.subheader(f'Price Over Time for {selected_product}')
        price_fig = px.line(filtered_df, x='date', y='price',
                            title=f'Product Price Over Time - {selected_product}',
                            labels={'date': 'Date', 'price': 'Price'})
        price_fig.update_layout(xaxis_title="Date", yaxis_title="Price ($)")
        st.plotly_chart(price_fig)

        # Display the data table with stock difference and price
        st.subheader('Stock and Price Data')
        display_df = filtered_df[['date', 'stock_amount', 'stock_difference', 'price', 'stock_id']].copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['stock_change'] = display_df['stock_difference'].apply(format_stock_difference)
        
        st.dataframe(display_df[['date', 'stock_amount', 'stock_change', 'price']], width=800)

        # Display current stock, price, and change from previous record
        if len(filtered_df) > 1:
            current_stock = int(filtered_df['stock_amount'].iloc[-1])
            previous_stock = int(filtered_df['stock_amount'].iloc[-2])
            stock_change = int(current_stock - previous_stock)
            
            current_price = filtered_df['price'].iloc[-1]
            previous_price = filtered_df['price'].iloc[-2]
            price_change = current_price - previous_price
            
            st.subheader("Current Stock and Price Information")
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Stock", current_stock, delta=stock_change)
            col2.metric("Previous Stock", previous_stock)
            col3.metric("Current Price", f"${current_price:.2f}", delta=f"${price_change:.2f}")

        # Screenshot viewer
        st.subheader("Screenshot Viewer")
        selected_date = st.selectbox("Select a date to view the screenshot", options=display_df['date'])
        selected_stock_id = display_df[display_df['date'] == selected_date]['stock_id'].values[0]

        screenshot_data = get_screenshot(selected_stock_id)
        if screenshot_data:
            try:
                image = Image.open(io.BytesIO(screenshot_data))
                st.image(image, caption=f"Screenshot from {selected_date}", use_column_width=True)
            except Exception as e:
                st.error(f"Error displaying image: {str(e)}")
        else:
            st.warning("No screenshot available for the selected date.")

    else:
        st.warning('No data available for the selected filters.')

if __name__ == "__main__":
    main()