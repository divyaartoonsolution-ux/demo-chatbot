from agents.memory import Session
from typing import List
import mysql.connector
from datetime import datetime
import ast,re,json
from dotenv import load_dotenv
import os

load_dotenv()  # loads variables from .env into environment

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

class MyCustomSession(Session):
    def __init__(self,session_id : str):
        self.session_id = session_id

    async def get_items(self, limit: int | None = None) -> List[dict]:

        """Fetch previous chat logs from MySQL."""
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT message_id, customer_id, user_message, bot_reply, intent_detected, timestamp
                FROM chatlogs
                WHERE customer_id = %s
                ORDER BY message_id ASC
            """

            cursor.execute(query, (self.session_id,))
            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            items = []
            for row in rows:
                if row['user_message']:
                    items.append({
                        "role": "user",
                        "content": row['user_message'],
                    })
                if row['bot_reply']:
                    items.append({
                        "role": "assistant",
                        "content": row['bot_reply']
                    })

            return items[-limit:] if limit else items

        except Exception as e:
            print("DB Read Error:", e)
            return []
    

    async def add_items(self, items: List[dict]) -> None:
        """Store user & bot text along with intent in chatlogs table."""
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            def extract_clean_text(data):
                if isinstance(data, str):
                    cleaned = data.strip().replace("```json", "").replace("```", "").strip()
                    try:
                        parsed = json.loads(cleaned.replace("'", '"'))
                        if isinstance(parsed, dict) and "text" in parsed:
                            data = parsed["text"]
                        else:
                            data = str(parsed)
                    except Exception:
                        try:
                            parsed = ast.literal_eval(cleaned)
                            if isinstance(parsed, dict) and "text" in parsed:
                                data = parsed["text"]
                            else:
                                data = str(parsed)
                        except Exception:
                            data = cleaned

                elif isinstance(data, dict):
                    return extract_clean_text(data.get("text", ""))

                elif isinstance(data, list):
                    return " ".join(extract_clean_text(d) for d in data)

                text = str(data).strip()
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
                text = re.sub(r'\*(.*?)\*', r'\1', text)
                text = re.sub(r'`(.*?)`', r'\1', text)
                text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
                text = re.sub(r'#+ ', '', text)
                return text.strip()

            for i in range(0, len(items), 2):
                if i + 1 >= len(items):
                    break

                user_raw = items[i].get("content", "")
                bot_raw = items[i + 1].get("content", "")
                intent = items[i].get("intent", "unknown")

                user_message = extract_clean_text(user_raw)
                bot_reply = extract_clean_text(bot_raw)

                query = """
                    INSERT INTO chatlogs (customer_id, user_message, bot_reply, intent_detected, session_id)
                    VALUES (%s, %s, %s, %s, %s)
                """

                params = (
                    str(self.session_id),      
                    str(user_message),
                    str(bot_reply),
                    str(intent),
                    str(self.session_id)
                )

                try:
                    cursor.execute(query, params)
                except Exception as e:
                    print("DB Write Error:", e)


            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            print("DB Write Error:", e)

    
    async def pop_item(self):
        return None  # Not implemented

    async def clear_session(self):
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chatlogs WHERE customer_id = %s", (self.session_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("Clear Session Error:", e)