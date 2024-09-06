import scrapy
from scrapy.crawler import CrawlerProcess
from bs4 import BeautifulSoup
import json
import re
import sqlite3
from datetime import datetime
import time

class StockSpider(scrapy.Spider):
    name = 'stock_spider'
    
    def __init__(self, *args, **kwargs):
        super(StockSpider, self).__init__(*args, **kwargs)
        self.conn = sqlite3.connect('product_database.db')
        self.cursor = self.conn.cursor()
        self.setup_database()
        self.current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open('product_data.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                subcategory TEXT,
                product_name TEXT,
                product_link TEXT UNIQUE,
                price REAL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                date TEXT,
                stock_amount INTEGER,
                FOREIGN KEY (product_id) REFERENCES product_info (id)
            )
        ''')
        self.conn.commit()

    def start_requests(self):
        for category, subcategories in self.data.items():
            for subcategory, subcategory_data in subcategories.items():
                for product in subcategory_data['products']:
                    translate_url = f"{product['link']}"
                    yield scrapy.Request(
                        url=translate_url,
                        callback=self.parse,
                        meta={
                            'category': category,
                            'subcategory': subcategory,
                            'product_name': product['Name'],
                            'product_link': product['link']
                        },
                        dont_filter=True
                    )

    def parse(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        
        # Extract stock number
        text_div = soup.find('div', class_='text collapse')
        stock = None
        if text_div:
            text_content = text_div.find('p').get_text(strip=True)
            number_match = re.search(r'\b\d+\b', text_content)
            if number_match:
                stock = int(number_match.group(0))
        
        # Extract price
        price_block = soup.find('div', class_='price-block')
        price = None
        if price_block:
            price_span = price_block.find('span', class_='woocommerce-Price-amount amount')
            if price_span:
                price_text = price_span.get_text(strip=True)
                price_match = re.search(r'[\d,]+(?:\.\d{2})?', price_text)
                if price_match:
                    price = float(price_match.group(0).replace(',', ''))

        pieces = None
        price_per_piece_div = soup.find('div', class_='price-per-piece')
        if price_per_piece_div:
            pieces_match = re.search(r'\b\d+\b', price_per_piece_div.get_text(strip=True))
            if pieces_match:
                pieces = int(pieces_match.group(0))
        if price is not None and pieces is not None:
            combined_price_info = f"{price} for {pieces} pieces"
        else:
            combined_price_info = None
        price=combined_price_info
        # Insert or update product info
        self.cursor.execute('''
            INSERT OR REPLACE INTO product_info (category, subcategory, product_name, product_link, price)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            response.meta['category'],
            response.meta['subcategory'],
            response.meta['product_name'],
            response.meta['product_link'],
            price
        ))
        
        # Get the product_id
        product_id = self.cursor.execute(
            'SELECT id FROM product_info WHERE product_link = ?', (response.meta['product_link'],)
        ).fetchone()[0]
        
        # Insert stock data
        self.cursor.execute('''
            INSERT INTO stock_data (product_id, date, stock_amount)
            VALUES (?, ?, ?)
        ''', (product_id, self.current_datetime, stock))
        
        self.conn.commit()

        yield {
            'category': response.meta['category'],
            'subcategory': response.meta['subcategory'],
            'product_name': response.meta['product_name'],
            'product_link': response.meta['product_link'],
            'stock_amount': stock,
            'price': price,
            'date': self.current_datetime
        }

    def closed(self, reason):
        self.conn.close()
        self.logger.info("Product and stock data have been saved to the SQLite database.")

def main():
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2,  # 2 second delay between requests
        'CONCURRENT_REQUESTS': 1  # Only one concurrent request
    })

    process.crawl(StockSpider)
    process.start()

if __name__ == "__main__":
    main()