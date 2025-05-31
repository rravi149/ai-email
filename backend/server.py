from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from openai import OpenAI

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# OpenAI client
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class EmailRequest(BaseModel):
    email_content: str
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None

class EmailReply(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tone: str
    content: str
    preview: str

class EmailRepliesResponse(BaseModel):
    replies: List[EmailReply]
    original_email: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "AI Email Helper API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

def generate_reply_with_tone(email_content: str, tone: str, sender_name: str = None) -> str:
    """Generate an email reply with specified tone using OpenAI GPT-4"""
    
    tone_prompts = {
        "professional": "Write a professional, formal email reply. Use appropriate business language and maintain a courteous tone.",
        "friendly": "Write a warm, friendly email reply. Use a conversational tone while remaining respectful and positive.",
        "brief": "Write a concise, direct email reply. Get straight to the point while remaining polite. Keep it short and clear.",
        "detailed": "Write a comprehensive, empathetic email reply. Provide thorough responses and show understanding of the sender's concerns."
    }
    
    sender_context = f" The sender's name is {sender_name}." if sender_name else ""
    
    system_prompt = f"""You are an AI email assistant that helps users craft appropriate email replies. {tone_prompts.get(tone, tone_prompts['professional'])}

Guidelines:
- Match the formality level of the original email
- Be helpful and responsive to their requests/questions
- Keep the reply relevant to the original email content
- Sign off appropriately for the tone
- Don't include subject lines or email headers
- Just provide the email body content{sender_context}"""

    user_prompt = f"""Please write a {tone} email reply to the following email:

---
{email_content}
---

Write only the email body content (no subject line or headers)."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@api_router.post("/generate-replies", response_model=EmailRepliesResponse)
async def generate_email_replies(request: EmailRequest):
    """Generate 4 different email replies with different tones"""
    
    if not request.email_content.strip():
        raise HTTPException(status_code=400, detail="Email content cannot be empty")
    
    tones = ["professional", "friendly", "brief", "detailed"]
    replies = []
    
    try:
        for tone in tones:
            content = generate_reply_with_tone(
                request.email_content, 
                tone, 
                request.sender_name
            )
            
            # Create a preview (first 100 characters)
            preview = content[:100] + "..." if len(content) > 100 else content
            
            reply = EmailReply(
                tone=tone,
                content=content,
                preview=preview
            )
            replies.append(reply)
        
        # Store the generated replies in database for potential future reference
        email_session = {
            "id": str(uuid.uuid4()),
            "original_email": request.email_content,
            "sender_name": request.sender_name,
            "sender_email": request.sender_email,
            "replies": [reply.dict() for reply in replies],
            "created_at": datetime.utcnow()
        }
        
        await db.email_sessions.insert_one(email_session)
        
        return EmailRepliesResponse(
            replies=replies,
            original_email=request.email_content
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating replies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate email replies")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
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
