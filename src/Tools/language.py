from agents import function_tool
import string

@function_tool
async def multi_language(user_input: str) -> str:
    """
    Detects greeting language from keywords and responds naturally
    in the same language but in Roman script (English letters).
    Offline, no external libraries.
    """

    # Clean and lowercase the input for matching
    cleaned_input = user_input.lower().translate(str.maketrans('', '', string.punctuation))

    # Language greeting → natural Roman script reply mappings
    greetings_map = {
        # Gujarati
        "gujarati": {
            "keywords": {"kem cho", "majama", "namaskar", "ram ram"},
            "reply": "Majama! Tame kem cho?"
        },
        # Hindi
        "hindi": {
            "keywords": {"namaste", "kaise ho", "kya haal", "namaskar"},
            "reply": "Namaste! Aap kaise ho?"
        },
        # Punjabi
        "punjabi": {
            "keywords": {"sat sri akal", "tussi thik ho", "ki haal"},
            "reply": "Tussi thik to assi vi thik?"
        },
        # Marathi
        "marathi": {
            "keywords": {"namaskar", "kasa kai", "tumhi kase", "kai chalay"},
            "reply": "Namaskar! Tumhi kase ahat?"
        },
        # Spanish
        "spanish": {
            "keywords": {"hola", "buenos dias", "como estas"},
            "reply": "Hola! Como estas?"
        },
        # French
        "french": {
            "keywords": {"bonjour", "salut", "ca va"},
            "reply": "Salut! Comment ca va?"
        },
        # English
        "english": {
            "keywords": {"hi", "hello", "hey", "good morning", "good evening"},
            "reply": "Hey! How are you?"
        }
    }

    # Detect language by keyword match
    for lang, data in greetings_map.items():
        if any(word in cleaned_input for word in data["keywords"]):
            return data["reply"]

    # Default fallback if no match found
    return "Hello! How are you?"
