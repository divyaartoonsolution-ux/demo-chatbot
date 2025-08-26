from litellm.exceptions import RateLimitError
from agents import Agent, Runner, set_tracing_disabled
from dotenv import load_dotenv
import uuid
import os
import asyncio

# --- Tools ---
from src.core.config import MyCustomSession
from src.Tools.instructions import instructions
from src.Tools.user import manage_user
from src.Tools.NLU import chatbot_engine_NLU
from src.Tools.language import multi_language
from src.Tools.product_discover import get_all_products
from src.Tools.Availability_check import availability_checker_tool
from src.Tools.Quote_generator import generate_quote
from src.Tools.order_placement import order_placement
from src.Tools.tech_QA_assistant import QA_assistant
from src.Tools.support_bot import create_support_ticket
from src.Tools.shipping_tool import shipping_calculator

# --- FastAPI ---
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# -------------------------------------------------
# ENV + KEYS
# -------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Disable tracing for cleaner logs
set_tracing_disabled(True)

# -------------------------------------------------
# AGENT SETUP
# -------------------------------------------------
model = "litellm/gemini/gemini-2.5-flash"

agent = Agent(
    name="Assistant",
    instructions=instructions,
    model=model,
    tools=[
        manage_user,
        chatbot_engine_NLU,
        multi_language,
        get_all_products,
        availability_checker_tool,
        generate_quote,
        order_placement,
        QA_assistant,
        create_support_ticket,
        shipping_calculator,
    ],
)


# One session (could extend for per-user sessions later)
SESSION_ID = str(uuid.uuid4())
session = MyCustomSession(SESSION_ID)

# -------------------------------------------------
# FASTAPI APP
# -------------------------------------------------
app = FastAPI()

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
# Chat UI
@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

# Chat API
@app.post("/chat")
async def chat_api(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    # Run agent
    result = await Runner.run(agent, input=user_message, session=session)

    return JSONResponse({"reply": result.final_output})








































# # Unique Session ID
# SESSION_ID = str(uuid.uuid4())
# print("Session ID:", SESSION_ID)


# BOT_ICON = "💻"
# USER_ICON = "🧑"

# async def main():
#     session = MyCustomSession(SESSION_ID)
#     print("🤖 Agent is Ready. Type your question ('exit' to quit).\n")
    
#     while True:
#         user_input = input(f"{USER_ICON} You: ")
#         if user_input.strip().lower() in ["exit", "quit"]:
#             print("👋 Bye!")
#             break

#         result = await Runner.run(agent, input=user_input, session=session)
#         print(f"{BOT_ICON} Bot:", result.final_output)

# if __name__ == "__main__":
#     asyncio.run(main())
















