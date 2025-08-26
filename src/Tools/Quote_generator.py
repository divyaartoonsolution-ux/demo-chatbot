import os
import json
import mysql.connector
from typing import Optional, List
from pydantic import BaseModel
from agents import function_tool
from dotenv import load_dotenv
from uuid import uuid4
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

load_dotenv()

# --- Constants ---
TAX_RATE = 0.18
DISCOUNTS = {'military': 0.15, 'corporate': 0.10, 'research': 0.05, 'guest': 0.0}
VERIFIED_BONUS = 0.02
BASE_SHIPPING = 25.0   # flat base shipping cost
PER_UNIT_FEE = 2.0     # cost per product unit

# --- Input Models ---
class QuoteRequestInput(BaseModel):
    product_name: str
    quantity: int
    customer_id: int

class QuoteItem(BaseModel):
    product_name: str
    unit_price: float
    quantity: int
    discount_percent: float
    discount_total: float
    subtotal: float

class QuoteOutput(BaseModel):
    quote_id: str
    customer_id: int
    customer_name: str
    items: List[QuoteItem]
    subtotal: float
    shipping_cost: float
    tax: float
    total: float
    currency: str = "USD"
    status: str = "generated"

# --- Shipping Calculator ---
def calculate_shipping_cost(quantity: int) -> float:
    """Simple shipping cost calculation: base + per unit fee"""
    return BASE_SHIPPING + (PER_UNIT_FEE * quantity)

# --- PDF Generator ---
def create_quote_pdf(quote: QuoteOutput, pdf_path: str):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []

    elements.append(Paragraph(f"Quote ID: {quote.quote_id}", styles["Title"]))
    elements.append(Paragraph(f"Customer: {quote.customer_name} (ID: {quote.customer_id})", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [["Product Name", "Unit Price", "Quantity", "Discount %", "Discount Total", "Subtotal"]]
    for item in quote.items:
        data.append([
            item.product_name,
            f"{item.unit_price:.2f} {quote.currency}",
            str(item.quantity),
            f"{item.discount_percent:.2f}%",
            f"{item.discount_total:.2f} {quote.currency}",
            f"{item.subtotal:.2f} {quote.currency}"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Subtotal: {quote.subtotal:.2f} {quote.currency}", styles["Normal"]))
    elements.append(Paragraph(f"Shipping: {quote.shipping_cost:.2f} {quote.currency}", styles["Normal"]))
    elements.append(Paragraph(f"Tax: {quote.tax:.2f} {quote.currency}", styles["Normal"]))
    elements.append(Paragraph(f"Total: {quote.total:.2f} {quote.currency}", styles["Normal"]))

    doc.build(elements)

# --- Main Function ---
@function_tool
def generate_quote(input: QuoteRequestInput) -> Optional[QuoteOutput]:
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        cursor = conn.cursor(dictionary=True)

        # Get user info
        cursor.execute("SELECT * FROM users WHERE id=%s", (input.customer_id,))
        user = cursor.fetchone()
        if not user:
            return "Customer not found."

        # Get product info
        cursor.execute("SELECT * FROM products WHERE product_name LIKE %s LIMIT 1", (f"%{input.product_name}%",))
        product = cursor.fetchone()
        if not product:
            return "Product not found."

        product_id = product['id']

        # Check inventory
        cursor.execute("SELECT quantity_left FROM inventory WHERE product_id=%s", (product_id,))
        inv = cursor.fetchone()
        if not inv or inv['quantity_left'] <= 0:
            return f"Product '{product['product_name']}' is out of stock."
        if input.quantity > inv['quantity_left']:
            return f"Only {inv['quantity_left']} units of '{product['product_name']}' are available."

        # Pricing
        unit_price = float(product['base_price'])
        quantity = input.quantity
        base_total = unit_price * quantity

        discount_percent = DISCOUNTS.get(user['user_type'].lower(), 0.0)
        if user['verified']:
            discount_percent += VERIFIED_BONUS

        discount_total = base_total * discount_percent
        subtotal = base_total - discount_total

        # Shipping cost
        shipping_cost = calculate_shipping_cost(quantity)

        # Tax on subtotal + shipping
        taxable_amount = subtotal + shipping_cost
        tax = taxable_amount * TAX_RATE
        total = taxable_amount + tax

        quote_id = f"Q-{str(uuid4())[:8]}"
        result = QuoteOutput(
            quote_id=quote_id,
            customer_id=input.customer_id,
            customer_name=user['full_name'],
            items=[QuoteItem(
                product_name=product['product_name'],
                unit_price=unit_price,
                quantity=quantity,
                discount_percent=round(discount_percent * 100, 2),
                discount_total=round(discount_total, 2),
                subtotal=round(subtotal, 2)
            )],
            subtotal=round(subtotal, 2),
            shipping_cost=round(shipping_cost, 2),
            tax=round(tax, 2),
            total=round(total, 2)
        )

        # Save quote
        items_data = [item.dict() for item in result.items]
        cursor.execute(
            "INSERT INTO quotes (quote_id, customer_id, items, subtotal, shipping_cost, tax, total, currency, status) "
            "VALUES (%s,%s,CAST(%s AS JSON),%s,%s,%s,%s,%s,%s)",
            (quote_id, input.customer_id, json.dumps(items_data), subtotal, shipping_cost, tax, total, "USD", "generated")
        )
        conn.commit()

        # Generate PDF
        pdf_dir = os.path.join(os.getcwd(), "quotes")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, f"quote_{quote_id}.pdf")
        create_quote_pdf(result, pdf_path)

        cursor.close()
        conn.close()
        return result

    except Exception as e:
        return f"Error generating quote: {str(e)}"
