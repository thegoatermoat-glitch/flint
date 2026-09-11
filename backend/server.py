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
import httpx


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
# FlintAI chat via OpenRouter (OpenAI-compatible). Stateless full-history
# contract so the SAME /api/ai/chat path is served by a Vercel serverless
# function in production and by this FastAPI backend in the Emergent preview.
# The OpenRouter key stays server-side (env var), never in the page source.
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.environ['OPENROUTER_API_KEY']
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = "google/gemini-3-flash-preview"  # OpenRouter model slug (Gemini 3 Flash)
DEFAULT_SYSTEM = "You are FlintAI, a helpful assistant."


class AITurn(BaseModel):
    role: str  # "user" | "assistant"
    text: str = ""
    images: List[str] = []  # data URLs, e.g. "data:image/png;base64,...."


class AIChatRequest(BaseModel):
    system: str = ""
    messages: List[AITurn] = []


def _to_openai_messages(req: AIChatRequest) -> list:
    msgs = [{"role": "system", "content": req.system or DEFAULT_SYSTEM}]
    for m in req.messages:
        if m.images:
            content = [{"type": "text", "text": m.text or ""}]
            for url in m.images:
                if url:
                    content.append({"type": "image_url", "image_url": {"url": url}})
            msgs.append({"role": m.role, "content": content})
        else:
            msgs.append({"role": m.role, "content": m.text or ""})
    return msgs


@api_router.post("/ai/chat")
async def ai_chat(req: AIChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages is required")

    payload = {
        "model": AI_MODEL,
        "messages": _to_openai_messages(req),
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://flin.space",
        "X-Title": "Flint",
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        data = r.json()
        if r.status_code >= 400 or "error" in data:
            msg = (data.get("error") or {}).get("message") if isinstance(data.get("error"), dict) else data.get("error")
            raise HTTPException(status_code=400, detail=msg or f"OpenRouter error ({r.status_code})")
        reply = data["choices"][0]["message"]["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("FlintAI chat error")
        raise HTTPException(status_code=400, detail=f"AI error: {e}")

    return {"reply": reply}

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