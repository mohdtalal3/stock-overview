# Product Stock Management System

This project is a **web-based Product Stock Management System** that allows users to track product stock levels and prices over time. It includes a web scraper to collect data, a database to store information, and a user interface for data visualization and analysis.

## Features

- **Web Scraper**: Automatically collects product information, stock levels, and prices from specified websites.
- **Data Storage**: Stores collected data in a SQLite database for easy access and management.
- **Stock Tracker**: Visualizes stock levels and price changes over time using interactive charts.
- **Product Overview**: Provides a comprehensive view of product stock and price changes across categories and subcategories.
- **Screenshot Capture**: Takes and stores screenshots of product pages for visual reference.

## Components

- **`main.py`**: The main Streamlit application that serves as the user interface.
- **`stock_spider.py`**: The web scraper built with Scrapy and Selenium to collect product data.
- **`stock_tracker.py`**: A module for visualizing and analyzing stock data.

## Setup and Usage

### Prerequisites
Make sure you have the following dependencies installed:
- Python 3.x
- Streamlit
- Scrapy
- Selenium (with the appropriate WebDriver)
- SQLite

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/mohdtalal3/stock-overview.git
    cd product-stock-management-system
    ```

### Running the Application

1. Start the Streamlit application:
    ```bash
    Click on run.bat file
    ```

2. Use the sidebar to navigate between different sections:
    - **Product Overview**: Get a summary of product stock levels and prices.
    - **Run Scraper**: Start the web scraper to collect the latest data.
    - **Stock Tracker**: Visualize and analyze stock and price trends.

## Data Visualization

The system provides interactive charts to help users visualize stock levels and price changes over time. Key features include:
- Tracking price fluctuations and stock levels for specific products.
- Viewing trends across different categories and subcategories.
- Accessing historical screenshots of product pages for reference.

## Example Usage

1. **Scraping Data**: Use the `Run Scraper` feature to automatically collect product data from supported websites.
2. **Tracking Stock & Prices**: Navigate to the `Stock Tracker` section to view interactive graphs of stock levels and prices.
3. **Product Overview**: View a detailed breakdown of product data across various categories and subcategories.


