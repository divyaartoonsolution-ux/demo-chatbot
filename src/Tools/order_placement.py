import os
import mysql.connector
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from agents import function_tool
from dotenv import load_dotenv
import json

load_dotenv()

# -----------------------------
# Pydantic Model for Input
# -----------------------------
class OrderPlacementInput(BaseModel):
    quote_id: str
    ship_to_address: str
    billing_address: Optional[str] = None
    payment_method: Optional[str] = None
    shipping_method: Optional[str] = None
    notes: Optional[str] = None

# -----------------------------
# Database Connection 
# -----------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        use_pure=True
    )

# -----------------------------
# Order Placement Tool
# -----------------------------
@function_tool
def order_placement(data: OrderPlacementInput) -> dict:
    """
    Creates an order from an approved quote and updates inventory.
    Stores items as proper JSON (no escaped slashes).
    Includes shipping_cost from quote.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Fetch the quote
        cursor.execute("SELECT * FROM quotes WHERE quote_id = %s", (data.quote_id,))
        quote = cursor.fetchone()

        if not quote:
            return {"error": f"Quote ID {data.quote_id} not found."}

        # Ensure items is a Python list/dict
        if isinstance(quote["items"], str):
            norm_items = json.loads(quote["items"])
        else:
            norm_items = quote["items"]

        # 2. Generate unique order ID
        order_id = f"O-{uuid4().hex[:8]}"

        # 3. Insert into orders table with CAST to JSON
        insert_query = """
        INSERT INTO orders (
            order_id, quote_id, customer_id, items, subtotal, tax, shipping_cost, total, currency,
            ship_to_address, billing_address, payment_method, payment_status,
            order_status, shipping_method, notes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            order_id,
            quote["quote_id"],
            quote["customer_id"],
            json.dumps(norm_items, ensure_ascii=False),  #  Convert dict/list to JSON string
            quote["subtotal"],
            quote["tax"],
            quote.get("shipping_cost", 0.0),  # ✅ added shipping_cost
            quote["total"],
            quote["currency"],
            data.ship_to_address,
            data.billing_address,
            data.payment_method,
            "pending",  # payment_status
            "pending",  # order_status
            data.shipping_method,
            data.notes
        ))

        # 4. Reduce inventory
        for item in norm_items:
            product_id = item.get("product_id")
            qty_ordered = item.get("quantity", 0)
            if product_id and qty_ordered > 0:
                cursor.execute("""
                    UPDATE inventory
                    SET quantity_left = quantity_left - %s
                    WHERE product_id = %s
                """, (qty_ordered, product_id))

        conn.commit()

        return {
            "message": "Order placed successfully and inventory updated.",
            "order_id": order_id,
            "quote_id": data.quote_id,
            "customer_id": quote["customer_id"],
            "shipping_cost": quote.get("shipping_cost", 0.0),
            "total": quote["total"],
            "currency": quote["currency"],
            "status": "pending"
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()
