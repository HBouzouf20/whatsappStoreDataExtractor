import os
import json
import re
import requests
import pandas as pd
from urllib.parse import urlparse

# Paths
har_folder = "./har-files"
image_folder = "./images"
os.makedirs(image_folder, exist_ok=True)

# Extract price from description
def extract_price(description):
    if not isinstance(description, str):
        return "No description"
    price_match = re.findall(r"~?(\d+)dh~?", description)
    return price_match[0] if price_match else "No price found"

# Extract brand from product name
def extract_brand(name):
    if not isinstance(name, str):
        return "Unknown"
    match = re.match(r"^([A-Z0-9]+)", name.strip())
    return match.group(1) if match else "Unknown"

# Extract product data
def extract_products_from_response(response_json, source_file):
    all_products = []

    collections = response_json.get("data", {}).get("xwa_product_catalog_get_single_collection", {})
    catalog = response_json.get("data", {}).get("xwa_product_catalog_get_product_catalog", {})

    if collections:
        collection = collections.get("collection", {})
        category_name = collection.get("name", "No Category")
        products = collection.get("products", [])
    elif catalog:
        category_name = "General Catalog"
        products = catalog.get("product_catalog", {}).get("products", [])
    else:
        return all_products

    for product in products:
        name = product.get("name", "No Name")
        image_path = "No image"

        if "media" in product and "images" in product["media"]:
            images = product["media"]["images"]
            if images:
                image_url = images[0].get("original_image_url", "")
                if image_url:
                    image_name = os.path.basename(urlparse(image_url).path)
                    image_path = os.path.join(image_folder, image_name)
                    try:
                        img_data = requests.get(image_url).content
                        with open(image_path, "wb") as img_file:
                            img_file.write(img_data)
                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading image: {e}")
                        image_path = "Error downloading image"

        product_info = {
            "sku": product.get("id", "No SKU"),
            "name": name,
            "price": extract_price(product.get("description", "")),
            "description": product.get("description", "No Description"),
            "category": category_name,
            "brand": extract_brand(name),
            "Source File": source_file,
            "Image Path": image_path,
        }

        all_products.append(product_info)

    return all_products

# Process all HAR files
all_products = []
for file_name in os.listdir(har_folder):
    if file_name.endswith(".har"):
        har_path = os.path.join(har_folder, file_name)
        try:
            with open(har_path, "r", encoding="utf-8") as file:
                har_data = json.load(file)
                for entry in har_data.get("log", {}).get("entries", []):
                    try:
                        response = entry["response"]
                        mime_type = response["content"].get("mimeType", "")
                        if "application/json" in mime_type:
                            response_text = response["content"].get("text", "")
                            if not response_text:
                                continue
                            response_json = json.loads(response_text)
                            products = extract_products_from_response(response_json, source_file=file_name)
                            all_products.extend(products)
                    except Exception as e:
                        print(f"Error processing entry in {file_name}: {e}")
        except Exception as e:
            print(f"Error reading {file_name}: {e}")

# Export to Excel
df = pd.DataFrame(all_products)
column_order = ["sku", "name", "price", "description", "category", "brand", "Source File", "Image Path"]
df = df[column_order]

excel_file_path = "product_data.xlsx"
df.to_excel(excel_file_path, index=False, sheet_name="Products")

print(f"Extracted {len(all_products)} products from {len(os.listdir(har_folder))} HAR files.")
print(f"Product data saved to {excel_file_path}")
print(f"Images saved to {image_folder}")
