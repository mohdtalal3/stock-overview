import scrapy
from scrapy.crawler import CrawlerProcess
from bs4 import BeautifulSoup
import json
import re
import sqlite3
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import io
from PIL import Image
from queue import Queue

class StockSpider(scrapy.Spider):
    name = 'stock_spider'
    
    def __init__(self, *args, message_queue=None, **kwargs):
        super(StockSpider, self).__init__(*args, **kwargs)
        self.conn = sqlite3.connect('product_database.db')
        self.cursor = self.conn.cursor()
        self.setup_database()
        self.current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.message_queue = message_queue
        
        with open('product_data.json', 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        
        self.log_message("Spider initialized. Starting to scrape...")

    def log_message(self, message):
        if self.message_queue:
            self.message_queue.put(message)
        self.logger.info(message)

    def setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                subcategory TEXT,
                product_name TEXT,
                product_link TEXT UNIQUE
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                date TEXT,
                stock_amount INTEGER,
                price REAL,
                screenshot BLOB,
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

    def take_screenshot(self, url):
        self.driver.get(url)
        time.sleep(2)  # Wait for the page to load
        screenshot = self.driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        image = image.convert('RGB')
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=70)
        return img_byte_arr.getvalue()

    def parse(self, response):
        self.log_message(f"Started scraping: {response.url}")
        
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

        # Take screenshot
        screenshot = self.take_screenshot(response.url)

        # Insert or ignore product info
        self.cursor.execute('''
            INSERT OR IGNORE INTO product_info (category, subcategory, product_name, product_link)
            VALUES (?, ?, ?, ?)
        ''', (
            response.meta['category'],
            response.meta['subcategory'],
            response.meta['product_name'],
            response.meta['product_link']
        ))
        
        # Get the product_id
        product_id = self.cursor.execute(
            'SELECT id FROM product_info WHERE product_link = ?', (response.meta['product_link'],)
        ).fetchone()[0]
        
        # Insert stock data, price, and screenshot
        self.cursor.execute('''
            INSERT INTO stock_data (product_id, date, stock_amount, price, screenshot)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, self.current_datetime, stock, price, sqlite3.Binary(screenshot)))
        
        self.conn.commit()

        self.log_message(f"Finished scraping: {response.url}")
        
        yield {
            'category': response.meta['category'],
            'subcategory': response.meta['subcategory'],
            'product_name': response.meta['product_name'],
            'product_link': response.url,
            'stock_amount': stock,
            'price': price,
            'date': self.current_datetime
        }

    def closed(self, reason):
        self.conn.close()
        self.driver.quit()
        self.log_message("Spider closed. All URLs have been scraped.")

def run_spider(message_queue):
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1
    })

    process.crawl(StockSpider, message_queue=message_queue)
    process.start()

if __name__ == "__main__":
    run_spider(None)