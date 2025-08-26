import os 
import json
import mysql.connector
from typing import List, Optional
from pydantic import BaseModel
from agents import function_tool  # Your decorator
from dotenv import load_dotenv

load_dotenv()

# Define mapping for stock status
STATUS_MAPPING = {
    0: "Out of Stock",
    1: "In Stock",
    2: "Preorder",
    3: "Discontinued"
}

# Define schema
class ProductQueryOutput(BaseModel):
    id: int
    product_name: str
    category: str
    short_description: Optional[str]
    long_description: Optional[str]
    tech_specs: Optional[dict]
    base_price: float
    stock_status: str

@function_tool
def get_all_products() -> List[ProductQueryOutput]:
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        # print("Connected to MySQL")

        cursor = conn.cursor()
        query = """
            SELECT 
                id, 
                product_name, 
                category, 
                short_description, 
                long_description, 
                tech_specs, 
                base_price, 
                stock_status
            FROM products
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        products = []
        for row in rows:
            product = ProductQueryOutput(
                id=row[0],
                product_name=row[1],
                category=row[2],
                short_description=row[3],
                long_description=row[4],
                tech_specs=json.loads(row[5]) if row[5] else None,
                base_price=float(row[6]),
                stock_status=STATUS_MAPPING.get(row[7], "Unknown")  #  Mapping integer to string
            )
            products.append(product)

        cursor.close()
        conn.close()

        return products

    except Exception as e:
        print("Error:", str(e))
        return []  # return empty list on error
