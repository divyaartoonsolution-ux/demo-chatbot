from datetime import datetime, date
import mysql.connector
from typing import Optional
from pydantic import BaseModel, EmailStr
from agents import function_tool
from dotenv import load_dotenv
import os


load_dotenv()

# --- Pydantic Model ---
class User(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    company: Optional[str]
    user_type: str
    country: str
    age: int
    sign_up_date: date

# --- MySQL Connection ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


@function_tool
def manage_user(email: str, requested_category: Optional[str] = None) -> dict:
    """
    Retrieves a user profile from MySQL.
    - If verified → full access (run compliance + proceed).
    - If not verified → block with message only.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # --- Check if user exists by EMAIL ---
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        name = existing_user["full_name"]
        # print("Name : ",name)

        if not existing_user:
            return {
                "status": "not_found",
                "message": "User not found. Please create a profile first.",
                "next_step": "create_profile"
            }

        # --- Check verification status ---
        if existing_user.get("verified").lower() == "no":
            return {
                "status": "blocked",
                "message": "You are not eligible"
            }
        else:

            return {
                "status": "success",
                "message": f"Welcome back, {existing_user['full_name']}! "
                        "Your profile is verified and you have full access. "
                        "Let's proceed to product discovery.",
                "user": existing_user,
                "next_step": "discover_products"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            # "next_step": "blocked"
        }
