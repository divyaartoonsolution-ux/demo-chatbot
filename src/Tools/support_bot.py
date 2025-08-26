import json
import os
import mysql.connector
from agents import function_tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

class SupportTicketRequest(BaseModel):
    customer_id: int
    product_id: int
    issue_text: str
    status: str = Field("open", pattern="^(open|resolved)$")  # default 'open'

@function_tool
async def create_support_ticket(data: SupportTicketRequest) -> dict:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch all orders for the customer
        cursor.execute("SELECT items FROM orders WHERE customer_id = %s", (data.customer_id,))
        orders = cursor.fetchall()

        if not orders:
            cursor.close()
            conn.close()
            return {
                "answer": f"No orders found for customer ID {data.customer_id}.",
                "explanation": "Customer has no orders in the database."
            }

        # Check if product_id exists in any order's items JSON
        product_found = False
        for order in orders:
            items_json = order['items']
            items = json.loads(items_json)
            for item in items:
                if item.get('product_id') == data.product_id:
                    product_found = True
                    break
            if product_found:
                # Insert the support ticket
                insert_sql = """
                    INSERT INTO support_tickets (customer_id, product_id, issue_text, status)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (data.customer_id, data.product_id, data.issue_text, data.status))
                conn.commit()

                ticket_id = cursor.lastrowid

                cursor.close()
                conn.close()

                return {
                    "answer": f"Support ticket #{ticket_id} created successfully.",
                    "explanation": "Your issue has been logged and will be addressed shortly."
                }


        if not product_found:
            cursor.close()
            conn.close()
            return {
                "answer": "Cannot create ticket.",
                "explanation": "No order found containing this product for your customer ID."
            }
        

        
    except mysql.connector.Error as e:
        return {
            "answer": "Failed to create support ticket.",
            "explanation": f"Database error: {e}"
        }
