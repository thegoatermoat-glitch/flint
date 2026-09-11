from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks


# ---------------------------------------------------------------------------
# FlintAI chat (Google Gemini 3 Flash via the Emergent universal LLM key).
# Stateless full-history contract so the SAME /api/ai/chat path is served by a
# Vercel serverless function (Google key) in production and by this FastAPI
# backend (Emergent key) in the Emergent preview.
# ---------------------------------------------------------------------------
EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']
AI_MODEL = ("gemini", "gemini-3-flash-preview")
DEFAULT_SYSTEM = "You are FlintAI, a helpful assistant."


class AITurn(BaseModel):
    role: str  # "user" | "assistant"
    text: str = ""
    images: List[str] = []  # data URLs, e.g. "data:image/png;base64,...."


class AIChatRequest(BaseModel):
    system: str = ""
    messages: List[AITurn] = []


def _strip_data_url(u: str) -> str:
    if u.startswith("data:") and "," in u:
        return u.split(",", 1)[1]
    return u


@api_router.post("/ai/chat")
async def ai_chat(req: AIChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages is required")

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=str(uuid.uuid4()),
        system_message=req.system or DEFAULT_SYSTEM,
    ).with_model(*AI_MODEL)

    # LlmChat can't be pre-seeded with prior turns, so flatten earlier turns
    # into a transcript that precedes the latest user message (keeps context
    # while staying fully stateless).
    prior, last = req.messages[:-1], req.messages[-1]
    parts = []
    if prior:
        transcript = "\n".join(
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.text}" for m in prior if m.text
        )
        if transcript:
            parts.append("Previous conversation:\n" + transcript + "\n\nCurrent message:")
    parts.append(last.text or "")
    text = "\n".join(parts)

    file_contents = [ImageContent(image_base64=_strip_data_url(u)) for u in (last.images or []) if u]
    user_msg = UserMessage(text=text, file_contents=file_contents) if file_contents else UserMessage(text=text)

    try:
        reply = await chat.send_message(user_msg)
    except Exception as e:
        logger.exception("FlintAI chat error")
        raise HTTPException(status_code=502, detail=f"AI error: {e}")

    return {"reply": reply if isinstance(reply, str) else str(reply)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()