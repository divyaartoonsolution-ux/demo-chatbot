import os
import mysql.connector
from pydantic import BaseModel
from typing import Literal
from dotenv import load_dotenv
from agents import function_tool

load_dotenv()

# ---------------------------
# Pydantic model for inputs
# ---------------------------
class LeadInput(BaseModel):
    customer_id: int
    budget_range: str  # e.g. "$10k-$50k"
    project_type: str  # e.g. "security upgrade", "R&D project"
    urgency: Literal["low", "medium", "high"]


# ---------------------------
# Tool function
# ---------------------------
@function_tool
async def lead_qualification(data: LeadInput) -> dict:
    """
    Qualifies a lead based on budget range, project type, and urgency.
    Saves the result into the Leads table.
    """

    # ---------------------------
    # Step 1: Scoring logic
    # ---------------------------
    budget_low = None
    try:
        # Extract first number from budget range for scoring
        budget_low = int("".join(filter(str.isdigit, data.budget_range.split('-')[0])))
    except Exception:
        budget_low = 0

    # Define lead quality rules
    if data.urgency == "high" and budget_low >= 50000:
        lead_score = "hot"
        qualified = "yes"
    elif data.urgency in ["medium", "high"] and budget_low >= 10000:
        lead_score = "warm"
        qualified = "yes"
    else:
        lead_score = "cold"
        qualified = "no"

    # ---------------------------
    # Step 2: Save to database
    # ---------------------------
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO Leads (customer_id, budget_range, project_type, urgency, qualified)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        data.customer_id,
        data.budget_range,
        data.project_type,
        data.urgency,
        qualified
    ))
    conn.commit()
    cursor.close()
    conn.close()

    # ---------------------------
    # Step 3: Return result
    # ---------------------------
    return {
        "lead_score": lead_score,
        "qualified": qualified,
        "message": f"Lead marked as {lead_score.upper()} (qualified: {qualified})"
    }
