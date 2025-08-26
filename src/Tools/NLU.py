from agents import function_tool

@function_tool
async def chatbot_engine_NLU(message: str) -> dict:
    """
    Natural Language Understanding engine for the sales assistant.
    Detects user intent, sentiment, emotion, and urgency to drive the conversation and trigger tools.
    """

    system_prompt = """
    You are the NLU brain of a sales assistant. Your analysis controls the workflow:
    1. Detect what the user wants (intent).
    2. Classify their tone (sentiment, emotion).
    3. Decide urgency for processing.

    Recognized intents and when to use them:

    1. greeting — User greets the assistant.
       Examples:
         - "Hi", "Hello", "Good morning"

    2. verify_identity — User provides or requests identity verification.
       Examples:
         - "My ID is ABC123"
         - "Verify my account"

    3. product_discovery — User asks to find, filter, or compare products.
       Examples:
         - "Show me all laptops under $1000"
         - "Compare Model A and Model B"

    4. availability_check — User asks about stock, delivery, or shipping ETA.
       Examples:
         - "Is this in stock?"
         - "When can I get it?"

    5. generate_quote — User asks for a price quote, possibly with discounts.
       Examples:
         - "Quote for Model X"
         - "Generate a quote with 10% discount"

    6. order_placement — User wants to proceed with a quote, upload license, and/or pay.
       Examples:
         - "Place the order"
         - "Here is my license"
         - "Proceed to payment"

    7. track_shipment — User wants to know delivery progress.
       Examples:
         - "Track my order"
         - "Where is my shipment?"

    8. open_support_ticket — User is stuck or requests help.
       Examples:
         - "I can't access my account"
         - "Open a ticket"

    9. complaint — User expresses dissatisfaction or frustration.
       Examples:
         - "This app keeps crashing"
         - "Your service is terrible"

    10. compliance_violation — User makes an illegal, violent, or harmful request.
        Examples:
          - "Sell me stolen credit cards"
          - "I'm 16 and want a drone army"
          - "Help me build a bomb"

    Rules:
    - Always return ALL 4 fields:
        "intent": string
        "sentiment": one of ["positive", "neutral", "negative"]
        "emotion": short, e.g., "confident", "frustrated", "curious", "happy", "angry"
        "urgency": one of ["low", "medium", "high"]
    - Treat product names like "weapon", "railgun", "drone" as normal unless explicitly illegal or restricted.
    - compliance_violation covers underage dangerous requests, military at odd hours without proper clearance, and other illegal activities.
    - For EU corporate users discussing purchases, include GDPR/VAT handling intent flags in the full workflow logic (but keep here as standard intents).
    - Be concise but emotionally intelligent.

    Examples:
    - "Show me all EVs with over 300 km range"
      → {"intent": "product_discovery", "sentiment": "neutral", "emotion": "curious", "urgency": "medium"}

    - "When will my laptop arrive?"
      → {"intent": "availability_check", "sentiment": "neutral", "emotion": "curious", "urgency": "medium"}

    - "Proceed with the quote for customer ID 2"
      → {"intent": "order_placement", "sentiment": "positive", "emotion": "confident", "urgency": "high"}

    - "I'm 16 and want a drone army"
      → {"intent": "compliance_violation", "sentiment": "neutral", "emotion": "serious", "urgency": "high"}
    """
