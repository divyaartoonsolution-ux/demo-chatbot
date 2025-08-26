import os
import mysql.connector
from agents import function_tool
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


"""
    Real-time inventory stock checker tool with auto stock_status update.

    Parameters:
    - product_id: Required. ID of the product to check inventory for.
    - requested_quantity: Optional. Number of units the user wants.
    - warehouse_location: Optional. Specific warehouse to check in.

    Behavior:
    - Checks real-time stock from inventory.
    - Auto-updates products.stock_status if quantity hits 0 or goes above 0.
    - If `requested_quantity` is given, it checks if that quantity is available.
    - If `warehouse_location` is provided, it filters the query by location.
    """



@function_tool
def availability_checker_tool(
    product_id: int,
    requested_quantity: int = None,
    warehouse_location: str = None,
) -> str:
    
    conn = None
    cursor = None

    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = conn.cursor(dictionary=True)

        # Step 1: Get inventory for product
        query = "SELECT quantity_left, warehouse_location, last_counted FROM inventory WHERE product_id = %s"
        params = [product_id]

        # if warehouse_location:
        #     query += " AND LOWER(warehouse_location) = %s"
        #     params.append(warehouse_location.lower())

        cursor.execute(query,params)
        results = cursor.fetchall()

        if not results:
            return "No inventory data found for that product."

        # Step 2: Calculate total stock
        total_quantity = sum(r["quantity_left"] for r in results)

        # Step 3: Update stock_status in products table
        new_status = "Out of Stock" if total_quantity == 0 else "In Stock"
        cursor.execute(
            "UPDATE products SET stock_status = %s WHERE id = %s",
            (new_status, product_id)
        )
        conn.commit()

        # Step 4: Handle quantity request
        if requested_quantity:
            if total_quantity >= requested_quantity:
                return f" Yes, {requested_quantity} units of product {product_id} are available."
            else:
                return f" Only {total_quantity} units available — not enough to fulfill {requested_quantity} units."

        # Step 5: Detailed stock breakdown
        details = "\n".join([
            f"- {r['quantity_left']} units in {r['warehouse_location']} (last counted {r['last_counted']})"
            for r in results
        ])
        return f" Available stock for product {product_id}:\n{details}"

    except Exception as e:
        return f" Error querying inventory: {str(e)}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



