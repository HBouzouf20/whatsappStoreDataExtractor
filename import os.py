import os
import json
import requests
import re
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from urllib.parse import urlparse

# Set the folder where the JSON file is stored
folder_path = "./json_data"  # Replace with your folder path
json_file_path = os.path.join(folder_path, "data_opt.json")

# Function to extract price from description
def extract_price(description):
    if not isinstance(description, str):
        return "No description"
    
    # Extract price between "~" symbols or "dh" for Moroccan Dirham
    price_match = re.findall(r'~(\d+)dh~', description)
    if not price_match:
        price_match = re.findall(r'(\d+)dh', description)
    
    return price_match[0] if price_match else "No price found"

# Load JSON data from the file
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# List to store all products
all_products = []

# Iterate over each catalog response
for catalog_response in data:
    catalog_name = catalog_response.get("name", "No Catalog Name")
    products = catalog_response.get("products", [])
    
    for product in products:
        product_info = {
            'catalog_name': catalog_name,
            'name': product.get('name', 'No Name'),
            'description': product.get('description', 'No Description'),
            'availability': product.get('product_availability', 'No Availability'),
            'sku': product.get('id', 'No SKU'),
            'url': product.get('url', 'No URL'),
        }
        
        # Extract price from description
        price = extract_price(product.get('description', ''))
        product_info['price'] = price
        
        # Handle images
        if 'image' in product:
            image_url = product['image']
            if image_url:
                image_name = os.path.basename(urlparse(image_url).path)
                image_path = os.path.join(folder_path, "images", image_name)
                
                # Download and save the image
                try:
                    img_data = requests.get(image_url).content
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    with open(image_path, 'wb') as img_file:
                        img_file.write(img_data)
                    product_info['image'] = image_name
                except requests.exceptions.RequestException as e:
                    print(f"Error downloading image: {e}")
                    product_info['image'] = "Error downloading image"
            else:
                product_info['image'] = "No image"
        else:
            product_info['image'] = "No image"

        # Add the product to the list
        all_products.append(product_info)

# Convert to DataFrame
df = pd.DataFrame(all_products)

# Save data to an Excel file
image_folder = os.path.join(folder_path, "images")
os.makedirs(image_folder, exist_ok=True)

excel_file_path = os.path.join(folder_path, "product_data.xlsx")
with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name="Products")

print(f"All product data saved to {excel_file_path} and images to {image_folder}")
