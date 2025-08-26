from pydantic import BaseModel
from agents import function_tool
from datetime import datetime, timedelta
import mysql.connector
import os
import json


# --- Input Model ---
class ShippingInput(BaseModel):
    customer_id: int
    product_id: int
    quantity: int
    hazmat: bool = False


# --- Output Model ---
class ShippingOutput(BaseModel):
    freight_cost: float
    eta_days: int
    estimated_delivery_date: str
    warehouse_location: str


# --- MySQL Connection ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# --- Shipping Calculator Tool ---
@function_tool
def shipping_calculator(input_data: ShippingInput) -> ShippingOutput:
    """
    Calculates freight cost & ETA based on user address, product weight,
    inventory warehouse, and hazmat rules.
    """

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # --- Step 1: Get user address ---
        cursor.execute(
            "SELECT country, state_province, city, postal_code FROM users WHERE id = %s",
            (input_data.customer_id,)
        )
        user = cursor.fetchone()
        if not user:
            raise ValueError("USER_NOT_FOUND")

        # --- Step 2: Get product weight ---
        cursor.execute("SELECT tech_specs FROM products WHERE id = %s", 
                       (input_data.product_id,))
        product = cursor.fetchone()
        if not product:
            raise ValueError("PRODUCT_NOT_FOUND")

        tech_specs = json.loads(product["tech_specs"])
        product_weight = tech_specs.get("weight_kg", 1.0)
        total_weight = product_weight * input_data.quantity

        # --- Step 3: Get warehouse info ---
        cursor.execute(
            "SELECT warehouse_location FROM inventory WHERE product_id = %s AND quantity_left > 0 LIMIT 1",
            (input_data.product_id,)
        )
        inventory = cursor.fetchone()
        if not inventory:
            raise ValueError("OUT_OF_STOCK")

        warehouse = inventory["warehouse_location"]

        # --- Step 4: Get shipping rules ---
        cursor.execute(
            "SELECT base_rate, per_kg_rate, hazmat_fee, avg_eta_days FROM shipping_rules WHERE country = %s",
            (user["country"],)
        )
        rule = cursor.fetchone()
        if not rule:
            raise ValueError("NO_SHIPPING_RULE")

        # --- Step 5: Calculate cost & ETA ---
        freight_cost = rule["base_rate"] + (total_weight * rule["per_kg_rate"])
        if input_data.hazmat:
            freight_cost += rule["hazmat_fee"]

        eta_days = rule["avg_eta_days"]
        estimated_date = (datetime.now() + timedelta(days=eta_days)).strftime("%Y-%m-%d")

        return ShippingOutput(
            freight_cost=round(freight_cost, 2),
            eta_days=eta_days,
            estimated_delivery_date=estimated_date,
            warehouse_location=warehouse
        )

    except ValueError as e:
        # Raise specific error codes for bot logic
        raise RuntimeError(str(e))

    except Exception as e:
        # Catch-all fallback
        raise RuntimeError("SYSTEM_ERROR")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
