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
# The key stays server-side. Per-session LlmChat instances keep multi-turn
# history in memory (keyed by the frontend's session_id).
# ---------------------------------------------------------------------------
EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']
AI_MODEL = ("gemini", "gemini-3-flash-preview")
DEFAULT_SYSTEM = "You are FlintAI, a helpful assistant."
_ai_chats: dict = {}


class AIChatRequest(BaseModel):
    session_id: str
    message: str
    system: str = ""
    images: List[str] = []  # raw base64 strings (no data: prefix)


@api_router.post("/ai/chat")
async def ai_chat(req: AIChatRequest):
    chat = _ai_chats.get(req.session_id)
    if chat is None:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=req.session_id,
            system_message=req.system or DEFAULT_SYSTEM,
        ).with_model(*AI_MODEL)
        _ai_chats[req.session_id] = chat

    file_contents = [ImageContent(image_base64=b64) for b64 in req.images if b64]
    if file_contents:
        user_msg = UserMessage(text=req.message, file_contents=file_contents)
    else:
        user_msg = UserMessage(text=req.message)

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