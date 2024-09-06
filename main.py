import requests
from bs4 import BeautifulSoup
import json
import time

def fetch_products(url):
    translate_url = f"{url}"
    response = requests.get(translate_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    products = []
    product_containers = soup.find_all('div', class_='product-small box')
    
    for container in product_containers:
        link_tag = container.find('a', class_='woocommerce-LoopProduct-link')
        link = link_tag['href'] if link_tag else None
        
        name_tag = container.find('p', class_='woocommerce-loop-product__title')
        name = name_tag.text.strip() if name_tag else None
        
        if name and link:
            products.append({
                "Name": name,
                "link": link
            })
    
    return products

# Main categories and their URLs
categories = {
    "Letterbox shipments": {
        "Envelops": "https://verpakgigant.nl/c/enveloppen/luchtkussen-enveloppen/standaard",
        "Letterbox Boxes": "https://verpakgigant.nl/c/verzenddozen/brievenbusdozen/alle/",
        "Plastic Shipping Bags": "https://verpakgigant.nl/c/verzendzakken/plastic-coex-verzendzakken",
        "Shipping labels": "https://verpakgigant.nl/c/magazijn-kantoor/papier-etiketten/verzendlabels"
    },
    "Boxes & Shipping Packaging": {
        "Single Wall Folding Boxes": "https://verpakgigant.nl/c/kartonnen-dozen/amerikaanse-vouwdozen/enkelgolf",
        "Double-wall folding boxes": "https://verpakgigant.nl/c/kartonnen-dozen/amerikaanse-vouwdozen/dubbelgolf",
        "Autolock Boxes": "https://verpakgigant.nl/c/verzenddozen/autolock-dozen",
        "Postal boxes": "https://verpakgigant.nl/c/verzenddozen/postdozen"
    },
    "Protection & Padding Material": {
        "Filler paper": "https://verpakgigant.nl/c/opvulmateriaal/opvulpapier/vulpapier/",
        "Bubble wrap": "https://verpakgigant.nl/c/beschermmateriaal/noppenfolie/alle-varianten/",
        "Flo-Pak Filler Chips": "https://verpakgigant.nl/c/opvulmateriaal/opvulchips",
        "Packaging tape": "https://verpakgigant.nl/c/magazijn-kantoor/tape/verpakkingstape"
    }
}

result = {}

for main_category, subcategories in categories.items():
    result[main_category] = {}
    for subcategory, url in subcategories.items():
        print(f"Fetching products for {main_category} - {subcategory}")
        result[main_category][subcategory] = {
            "url": url,
            "products": fetch_products(url)
        }
        time.sleep(2)  # Add a delay to avoid overloading the server

# Save the result to a JSON file
with open('product_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("Data has been saved to product_data.json")










