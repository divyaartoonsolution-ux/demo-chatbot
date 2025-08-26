from agents import function_tool
import mysql.connector
import os

# Example descriptions
PRODUCT_DB = {
    "Among Bot": "Among Bot is a firewall system that dynamically adapts firewall rules to ensure efficient network protection while minimizing resource use.",
    "Important Wall": "Important Wall is a versatile robot designed for stock management and organizational automation in warehouse environments.",
    "Republican Drone": "Republican Drone is a high-performance firewall device providing robust security for complex network infrastructures.",
    "Finally Blaster": "Finally Blaster is a tactical explosive device used for military training and controlled demolition exercises.",
    "Book Shield": "Book Shield is a weapon system engineered to provide reliable defense capabilities in tactical scenarios.",
    "Five Drone": "Five Drone is a robot built for versatile management tasks with enhanced navigation and sensing capabilities.",
    "Successful Wall": "Successful Wall is a firewall product designed to deliver strong perimeter protection with low false positive rates.",
    "Model Wall": "Model Wall is a compact weapon system optimized for rapid deployment and precision targeting.",
    "Film Bot": "Film Bot is a weapon system designed for controlled simulation effects in training and entertainment.",
    "Seat Wall": "Seat Wall is a firewall designed to establish robust network protection for enterprise environments.",
}

# DB connection function
def get_product_specs(product_name):
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT power_kW, range_km, weight_kg, price, 
               CASE availability WHEN 1 THEN 'In Stock' ELSE 'Out of Stock' END AS stock_status
        FROM products
        WHERE name = %s
    """
    cursor.execute(query, (product_name,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()
    return result

@function_tool
async def QA_assistant(message: str) -> dict:
    product_name = None
    for name in PRODUCT_DB:
        if name.lower() in message.lower():
            product_name = name
            break

    if product_name:
        description = PRODUCT_DB[product_name]
        specs = get_product_specs(product_name)

        if specs:
            # Format into a single natural paragraph
            answer = (
                f"{description} It has a power output of {specs['power_kW']} kW, "
                f"a range of {specs['range_km']} km, and weighs {specs['weight_kg']} kg. "
                f"The unit is priced at ${specs['price']:,} and is currently {specs['stock_status'].lower()}."
            )
            explanation = "Description and specifications combined into a single paragraph."
        else:
            answer = description
            explanation = "Specs not found in database, only description shown."
    else:
        answer = "Sorry, I couldn't identify the product you asked about."
        explanation = "Product name not found in the database."

    return {
        "answer": answer,
        "explanation": explanation
    }
