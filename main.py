"""
=============================================================================
WHATSAPP AI SALES AGENT - MAIN APPLICATION
=============================================================================
FastAPI application that handles WhatsApp webhook events and integrates
with the Groq AI engine (Llama 3) to power automated sales conversations.

Author: Your Agency Name
Version: 1.0.0
=============================================================================
"""

import os
import re
import logging
import asyncio
import httpx
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi import FastAPI, Request, HTTPException, Query, Form, File, UploadFile
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ai_engine import ai_engine
from database import db

# Load environment variables
load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

# WhatsApp API Configuration
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")  # Sandbox number

# Meta Graph API endpoint for sending messages
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# Evolution API Configuration (QR Code WhatsApp Gateway)
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "").rstrip("/")
EVOLUTION_API_GLOBAL_KEY = os.getenv("EVOLUTION_API_GLOBAL_KEY", "")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# APPLICATION LIFESPAN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 WhatsApp AI Sales Agent is starting up...")
    logger.info(f"📱 Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")
    
    # Validate required environment variables
    missing_vars = []
    if not WHATSAPP_ACCESS_TOKEN:
        missing_vars.append("WHATSAPP_ACCESS_TOKEN")
    if not WHATSAPP_VERIFY_TOKEN:
        missing_vars.append("WHATSAPP_VERIFY_TOKEN")
    if not WHATSAPP_PHONE_NUMBER_ID:
        missing_vars.append("WHATSAPP_PHONE_NUMBER_ID")
    
    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("The application will start but WhatsApp integration may not work.")
    else:
        logger.info("✅ All environment variables loaded successfully!")
    
    yield
    
    # Shutdown
    logger.info("👋 WhatsApp AI Sales Agent is shutting down...")


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="WhatsApp AI Sales Agent",
    description="An AI-powered sales agent that automates WhatsApp conversations using Gemini 1.5 Flash",
    version="1.0.0",
    lifespan=lifespan
)

# =============================================================================
# RATE LIMITING
# =============================================================================
# Protects API endpoints from brute force, scraping, and abuse.
# Default: 60 requests/minute per IP. Sensitive endpoints have stricter limits.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# =============================================================================
# CORS — Restrict API access to our own frontend domains
# =============================================================================
# Only allow requests originating from our Vercel-hosted frontend
# and the custom domain (once DNS is configured).
ALLOWED_ORIGINS = [
    "https://salesflow-ai-psi.vercel.app",
    "https://salesaiflow.online",
    "https://www.salesaiflow.online",
    "http://localhost:3000",   # Local development
    "http://localhost:5500",   # VS Code Live Server
    "http://127.0.0.1:5500",  # VS Code Live Server (alt)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)



# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_message_data(body: dict) -> Optional[tuple[str, str, str]]:
    """
    Extract the sender's phone number, message body, and message ID from
    the WhatsApp webhook payload.
    
    WhatsApp Webhook JSON Structure:
    {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "<WHATSAPP_BUSINESS_ACCOUNT_ID>",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "<BUSINESS_PHONE_NUMBER>",
                                "phone_number_id": "<PHONE_NUMBER_ID>"
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "<SENDER_NAME>"},
                                    "wa_id": "<SENDER_PHONE_NUMBER>"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "<SENDER_PHONE_NUMBER>",
                                    "id": "<MESSAGE_ID>",
                                    "timestamp": "<UNIX_TIMESTAMP>",
                                    "type": "text",
                                    "text": {
                                        "body": "<MESSAGE_CONTENT>"
                                    }
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    Args:
        body: The full webhook payload from WhatsApp
        
    Returns:
        Tuple of (phone_number, message_body, message_id, to_number) or None if not a valid message
    """
    try:
        # Navigate through the nested JSON structure
        entry = body.get("entry", [])
        if not entry:
            return None
        
        changes = entry[0].get("changes", [])
        if not changes:
            return None
        
        value = changes[0].get("value", {})
        
        # Check if this is a message event (not a status update)
        messages = value.get("messages", [])
        if not messages:
            logger.debug("No messages in payload - might be a status update")
            return None
        
        message = messages[0]
        
        # Extract the sender's phone number
        phone_number = message.get("from")
        
        # Extract the message ID (useful for tracking)
        message_id = message.get("id")
        
        # Extract the message content based on type
        message_type = message.get("type")
        
        if message_type == "text":
            # Standard text message
            message_body = message.get("text", {}).get("body", "")
        elif message_type == "button":
            # Quick reply button response
            message_body = message.get("button", {}).get("text", "")
        elif message_type == "interactive":
            # Interactive message response (list/button)
            interactive = message.get("interactive", {})
            interactive_type = interactive.get("type")
            if interactive_type == "button_reply":
                message_body = interactive.get("button_reply", {}).get("title", "")
            elif interactive_type == "list_reply":
                message_body = interactive.get("list_reply", {}).get("title", "")
            else:
                message_body = "[Interactive message]"
        else:
            # Handle other message types (image, audio, document, etc.)
            message_body = f"[{message_type.upper()} message received]"
            logger.info(f"Received non-text message type: {message_type}")
        
        # Extract the business receiving the message
        to_number = value.get("metadata", {}).get("display_phone_number")
        if to_number:
            to_number = to_number.replace("+", "")
        
        if phone_number and message_body:
            return (phone_number, message_body, message_id, to_number)
        
        return None
        
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error extracting message data: {str(e)}")
        return None


async def send_whatsapp_message(
    recipient_phone: str,
    message_text: str,
    access_token: str = None,
    phone_number_id: str = None
) -> bool:
    """
    Send a WhatsApp message via the Meta Graph API using per-business credentials.
    """
    token = access_token or WHATSAPP_ACCESS_TOKEN
    num_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID
    
    if not token or not num_id:
        logger.error("❌ WhatsApp API credentials not configured!")
        return False
        
    api_url = f"https://graph.facebook.com/v18.0/{num_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_text
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get("messages", [{}])[0].get("id", "unknown")
                logger.info(f"✅ Message sent successfully! ID: {message_id}")
                return True
            else:
                logger.error(f"❌ Failed to send message. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp message: {str(e)}")
        return False


async def send_whatsapp_image(
    recipient_phone: str,
    image_url: str,
    caption: str = "",
    access_token: str = None,
    phone_number_id: str = None
) -> bool:
    """
    Send a WhatsApp image message via the Meta Graph API.
    """
    token = access_token or WHATSAPP_ACCESS_TOKEN
    num_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID
    
    if not token or not num_id:
        logger.error("❌ WhatsApp API credentials not configured for image sending!")
        return False
        
    api_url = f"https://graph.facebook.com/v18.0/{num_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_phone,
        "type": "image",
        "image": {
            "link": image_url
        }
    }
    if caption:
        payload["image"]["caption"] = caption
        
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Image sent successfully to {recipient_phone}!")
                return True
            else:
                logger.error(f"❌ Failed to send image. Status: {response.status_code}, Response: {response.text}")
                return False
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp image: {str(e)}")
        return False


async def mark_message_as_read(
    message_id: str,
    access_token: str = None,
    phone_number_id: str = None
) -> bool:
    """
    Mark a received message as read (shows blue ticks to the sender).
    """
    token = access_token or WHATSAPP_ACCESS_TOKEN
    num_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID
    
    if not token or not num_id:
        return False
        
    api_url = f"https://graph.facebook.com/v18.0/{num_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=payload
            )
            return response.status_code == 200
    except Exception as e:
        logger.debug(f"Could not mark message as read: {str(e)}")
        return False


# =============================================================================
# WEBHOOK ENDPOINTS
# ================================================# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@app.get("/webhook/{business_id}")
async def verify_business_webhook(
    business_id: str,
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
) -> PlainTextResponse:
    """
    Per-business WhatsApp Webhook Verification Endpoint (GET).
    Looks up credentials in the database to verify the handshake.
    """
    logger.info(f"📥 Received webhook verification request for business: {business_id}")
    
    # Fetch business credentials
    creds = db.get_business_credentials(business_id)
    expected_token = creds.get("meta_verify_token")
    
    # Fallback to global verify token if no business-specific token exists yet
    if not expected_token:
        expected_token = WHATSAPP_VERIFY_TOKEN
        
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info(f"✅ Webhook verification successful for business: {business_id}!")
        # Mark as connected in the DB
        db.mark_webhook_verified(business_id)
        return PlainTextResponse(content=hub_challenge, status_code=200)
    else:
        logger.warning(f"❌ Webhook verification failed for business: {business_id} — token mismatch!")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/{business_id}")
async def handle_business_webhook(business_id: str, request: Request) -> JSONResponse:
    """
    Per-business WhatsApp Webhook Handler Endpoint (POST).
    Scores and routes incoming WhatsApp events directly for the specific business ID.
    """
    try:
        body = await request.json()
        logger.info(f"📨 Received webhook event for business {business_id}")
        logger.debug(f"Payload: {body}")
        
        message_data = extract_message_data(body)
        
        if message_data:
            phone_number, message_body, message_id, to_number = message_data
            logger.info(f"📱 Message from {phone_number} (scoped to business {business_id}): {message_body[:50]}...")
            
            # Save sender name if present
            try:
                contacts = body["entry"][0]["changes"][0]["value"].get("contacts", [])
                if contacts:
                    sender_name = contacts[0].get("profile", {}).get("name", "")
                    if sender_name:
                        db.update_contact_name(business_id, phone_number, sender_name)
            except (KeyError, IndexError):
                pass
            
            # Mark read using business credentials
            creds = db.get_business_credentials(business_id)
            access_token = creds.get("meta_access_token")
            phone_number_id = creds.get("meta_phone_number_id")
            await mark_message_as_read(message_id, access_token, phone_number_id)
            
            # Save user message to database immediately
            db.save_message(business_id, phone_number, "user", message_body)
            
            # Check human handoff
            if db.is_human_handoff(business_id, phone_number):
                if message_body.strip().lower() in ['resume bot', 'resume ai', '/resume']:
                    db.set_human_handoff(business_id, phone_number, False)
                    await send_whatsapp_message(
                        recipient_phone=phone_number,
                        message_text="bot is back online! how can i help you?",
                        access_token=access_token,
                        phone_number_id=phone_number_id
                    )
                else:
                    logger.info(f"🙋 Skipping AI response for {phone_number} (human handoff active)")
                return JSONResponse(content={"status": "ok"}, status_code=200)

            # Check if customer wants a human
            handoff_triggers = ['talk to someone', 'speak to someone', 'talk to a human', 'speak to a human', 'real person', 'i want a human', 'talk to a person', 'speak to a person', 'customer service', 'talk to owner', 'speak to owner', 'human agent']
            if any(trigger in message_body.lower() for trigger in handoff_triggers):
                db.set_human_handoff(business_id, phone_number, True)
                await send_whatsapp_message(
                    recipient_phone=phone_number,
                    message_text="no problem! i've notified the boss. someone will get back to you shortly. thanks for your patience 🙏",
                    access_token=access_token,
                    phone_number_id=phone_number_id
                )
                return JSONResponse(content={"status": "ok"}, status_code=200)
            
            # Process AI reply in background task
            asyncio.create_task(_process_and_reply_meta(business_id, phone_number, message_body, sender_name))
            
        return JSONResponse(content={"status": "ok"}, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error in per-business webhook: {str(e)}")
        return JSONResponse(content={"status": "ok"}, status_code=200)


@app.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
) -> PlainTextResponse:
    """
    Legacy Global WhatsApp Webhook Verification Endpoint (GET).
    """
    logger.info("📥 Received global webhook verification request")
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ Global webhook verification successful!")
        return PlainTextResponse(content=hub_challenge, status_code=200)
    else:
        logger.warning("❌ Global webhook verification failed - token mismatch!")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def handle_webhook(request: Request) -> JSONResponse:
    """
    Legacy Global WhatsApp Webhook Handler Endpoint (POST).
    """
    try:
        body = await request.json()
        logger.info("📨 Received global webhook event")
        message_data = extract_message_data(body)
        
        if message_data:
            phone_number, message_body, message_id, to_number = message_data
            
            # Look up the business ID based on the Meta WhatsApp number
            business_id = db.get_business_id_by_phone(to_number)
            if not business_id:
                logger.warning(f"⚠️ No business found for number {to_number}. Ignored.")
                return JSONResponse(content={"status": "ok"}, status_code=200)
            
            # Forward directly to the scoped webhook handler logic dynamically
            creds = db.get_business_credentials(business_id)
            access_token = creds.get("meta_access_token")
            phone_number_id = creds.get("meta_phone_number_id")
            
            try:
                contacts = body["entry"][0]["changes"][0]["value"].get("contacts", [])
                if contacts:
                    sender_name = contacts[0].get("profile", {}).get("name", "")
                    if sender_name:
                        db.update_contact_name(business_id, phone_number, sender_name)
            except (KeyError, IndexError):
                pass
            
            await mark_message_as_read(message_id, access_token, phone_number_id)
            
            if db.is_human_handoff(business_id, phone_number):
                if message_body.strip().lower() in ['resume bot', 'resume ai', '/resume']:
                    db.set_human_handoff(business_id, phone_number, False)
                    await send_whatsapp_message(
                        phone_number, 
                        "bot is back online! how can i help you?",
                        access_token,
                        phone_number_id
                    )
                return JSONResponse(content={"status": "ok"}, status_code=200)

            handoff_triggers = ['talk to someone', 'speak to someone', 'talk to a human', 'speak to a human', 'real person', 'i want a human', 'talk to a person', 'speak to a person', 'customer service', 'talk to owner', 'speak to owner', 'human agent']
            if any(trigger in message_body.lower() for trigger in handoff_triggers):
                db.set_human_handoff(business_id, phone_number, True)
                await send_whatsapp_message(
                    phone_number, 
                    "no problem! i've notified the boss. someone will get back to you shortly. thanks for your patience 🙏",
                    access_token,
                    phone_number_id
                )
                return JSONResponse(content={"status": "ok"}, status_code=200)
            
            asyncio.create_task(_process_and_reply_meta(business_id, phone_number, message_body, sender_name))
        
        return JSONResponse(content={"status": "ok"}, status_code=200)
    except Exception as e:
        logger.error(f"❌ Error processing global webhook: {str(e)}")
        return JSONResponse(content={"status": "ok"}, status_code=200)


async def extract_order_details_via_llm(business_id: str, phone_number: str, last_message: str) -> dict:
    """
    Query Groq to parse the order items, total amount, and delivery address
    from the recent conversation history.
    """
    try:
        # Get history (last 10 messages should be plenty for context)
        history = db.get_conversation_history(business_id, phone_number, limit=10)
        
        transcript = ""
        for msg in history:
            role = "Customer" if msg["role"] == "user" else "AI Agent"
            content = msg["parts"][0] if msg.get("parts") else ""
            transcript += f"{role}: {content}\n"
            
        # Add the last user message just in case it wasn't saved yet
        if last_message and last_message not in transcript:
            transcript += f"Customer: {last_message}\n"
            
        system_prompt = (
            "You are a precise data extractor. Analyze the WhatsApp conversation transcript between a Customer and an AI sales agent.\n"
            "Extract:\n"
            "1. Ordered items: A concise, human-readable summary of products and quantities (e.g., '1x Hennessy VS, 2x Jameson').\n"
            "2. Total amount: The final agreed total amount in Naira as an integer (e.g., 100000). If no clear total is agreed, calculate it based on the prices mentioned or set to 0. Do not include currency symbols or commas.\n"
            "3. Delivery address: The physical address mentioned by the customer. If no address has been provided yet, output null.\n\n"
            "Return ONLY a valid JSON object matching this schema, without any markdown formatting, backticks, or extra text:\n"
            "{\n"
            '  "items": "description of ordered items",\n'
            '  "total_amount": 100000,\n'
            '  "delivery_address": "address or null"\n'
            "}"
        )
        
        response = await ai_engine.client.chat.completions.create(
            model=ai_engine.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n{transcript}"}
            ],
            temperature=0.1,  # Low temperature for deterministic extraction
            max_tokens=200,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Strip any markdown code block wrapper if the model returns it
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n", "", content)
            content = re.sub(r"\n```$", "", content)
            
        import json
        data = json.loads(content)
        
        # Ensure correct types
        return {
            "items": str(data.get("items", last_message)),
            "total_amount": int(data.get("total_amount", 0)),
            "delivery_address": data.get("delivery_address") if data.get("delivery_address") else None
        }
    except Exception as e:
        logger.error(f"Error extracting order details via LLM: {e}")
        return {
            "items": last_message,
            "total_amount": 0,
            "delivery_address": None
        }


async def _process_and_reply_meta(business_id: str, phone_number: str, message_body: str, sender_name: str = None):
    """Background task: generate AI response, detect orders, then send via Meta Graph API."""
    try:
        # Simulate human typing delay (7 seconds) so it doesn't look like a bot
        await asyncio.sleep(7)
        
        # Get business credentials
        creds = db.get_business_credentials(business_id)
        access_token = creds.get("meta_access_token")
        phone_number_id = creds.get("meta_phone_number_id")
        
        # Generate AI response using AI Engine (Multi-Tenant)
        ai_response = await ai_engine.generate_response(
            business_id=business_id,
            phone_number=phone_number,
            user_message=message_body,
            save_user_message=False
        )
        
        if ai_response:
            # Check for AI-triggered handoff
            if "[HANDOFF_TRIGGERED]" in ai_response:
                ai_response = ai_response.replace("[HANDOFF_TRIGGERED]", "").strip()
                db.set_human_handoff(business_id, phone_number, True)
                logger.info(f"🙋 AI triggered human handoff for {phone_number}")

            # Dynamic Order Detection (Component 5)
            business_config = db.get_business_config(business_id)
            payment_info = business_config.get("payment_info", "")
            
            # Default fallback payment detection keywords
            payment_keywords = ["bank", "transfer", "opay", "account", "payment", "pay", "8137048851"]
            if payment_info:
                payment_keywords.extend([w.lower() for w in payment_info.split() if len(w) > 3])
                
            if any(keyword in ai_response.lower() for keyword in payment_keywords) and ("account" in ai_response.lower() or "number" in ai_response.lower() or "pay" in ai_response.lower() or "transfer" in ai_response.lower()):
                try:
                    customer_name = sender_name if sender_name else "Unknown"
                    order_details = await extract_order_details_via_llm(business_id, phone_number, message_body)
                    db.save_order(
                        business_id=business_id,
                        phone_number=phone_number,
                        customer_name=customer_name,
                        items=order_details["items"],
                        total_amount=order_details["total_amount"],
                        delivery_address=order_details["delivery_address"]
                    )
                    logger.info(f"📦 Order auto-detected and extracted for {phone_number}: {order_details}")
                except Exception as e:
                    logger.error(f"Error saving order: {e}")

            # Extract [IMAGE:product_id] tokens (Component 6)
            image_tokens = re.findall(r'\[IMAGE:([a-zA-Z0-9\-]+)\]', ai_response)
            
            # Strip image tokens from text response
            clean_response = re.sub(r'\[IMAGE:[a-zA-Z0-9\-]+\]', '', ai_response).strip()
            
            # Send clean text response first
            if clean_response:
                await send_whatsapp_message(
                    recipient_phone=phone_number,
                    message_text=clean_response,
                    access_token=access_token,
                    phone_number_id=phone_number_id
                )
            
            # Send images for each token
            for prod_id in image_tokens:
                product = db.get_product_by_id(prod_id)
                if product and product.get("image_url"):
                    # Parse multiple images if stored as a JSON array string
                    images_to_send = []
                    raw_url = product["image_url"]
                    if raw_url.startswith("[") and raw_url.endswith("]"):
                        try:
                            import json
                            images_to_send = json.loads(raw_url)
                        except Exception:
                            images_to_send = [raw_url]
                    else:
                        images_to_send = [raw_url]
                    
                    # Filter out empty URLs
                    images_to_send = [u for u in images_to_send if u]
                    
                    base_caption = f"{product['name']}"
                    if product.get('price'):
                        try:
                            price_val = float(product['price'])
                            base_caption += f" — ₦{price_val:,.0f}"
                        except Exception:
                            base_caption += f" — ₦{product['price']}"
                    
                    for i, img_url in enumerate(images_to_send):
                        img_caption = f"{base_caption} (Photo {i+1}/{len(images_to_send)})" if len(images_to_send) > 1 else base_caption
                        await send_whatsapp_image(
                            recipient_phone=phone_number,
                            image_url=img_url,
                            caption=img_caption,
                            access_token=access_token,
                            phone_number_id=phone_number_id
                        )
                    logger.info(f"🖼️ Sent {len(images_to_send)} product image(s) for {prod_id} to {phone_number} via Meta")
            
        else:
            logger.error("❌ AI engine returned empty response")
            
    except Exception as e:
        logger.error(f"❌ Background Meta reply error: {str(e)}")

@app.post("/twilio/webhook")
async def handle_twilio_webhook(
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    ProfileName: str = Form(None)
) -> PlainTextResponse:
    """
    Twilio WhatsApp Webhook Handler.
    Responds IMMEDIATELY with empty TwiML to avoid Twilio timeouts,
    then processes the AI response in the background and sends it
    via the Twilio REST API.
    """
    # Clean the sender phone number
    phone_number = From.replace("whatsapp:", "")
    to_number = To.replace("whatsapp:", "")
    logger.info(f"📨 Received Twilio message from {phone_number} to {to_number}: {Body[:50]}...")

    # --- SANDBOX MULTI-TENANT SWITCHER ---
    # Because Twilio Sandbox shares one number, we allow developers to switch the active business via a command
    logger.info("Checking for Sandbox Switcher command...")
    if Body.strip().lower().startswith("/test"):
        target_name = Body.strip()[5:].strip()
        try:
            # Search for the business by name
            res = db.client.table("businesses").select("id, name").ilike("name", f"%{target_name}%").execute()
            if res.data and len(res.data) > 0:
                db.set_sandbox_session(phone_number, res.data[0]["id"])
                logger.info(f"🔌 Sandbox user {phone_number} connected to {res.data[0]['name']}")
                
                # Send instant confirmation
                resp = MessagingResponse()
                resp.message(f"🔌 Connected to test bot: {res.data[0]['name']}. Send 'hi' to start!")
                return PlainTextResponse(str(resp), media_type="application/xml")
            else:
                resp = MessagingResponse()
                resp.message(f"❌ Could not find a business named '{target_name}'. Please check the exact name in your dashboard.")
                return PlainTextResponse(str(resp), media_type="application/xml")
        except Exception as e:
            logger.error(f"Error switching sandbox: {e}")

    # Look up business ID (Check Sandbox Sessions first, then fallback to database)
    business_id = db.get_sandbox_session(phone_number)
    if not business_id:
        business_id = db.get_business_id_by_phone(to_number)
        
    if not business_id:
        logger.warning(f"⚠️ No business found for number {to_number}. Ignored.")
        resp = MessagingResponse()
        return PlainTextResponse(str(resp), media_type="application/xml")

    # Save contact name if provided
    if ProfileName:
        db.update_contact_name(business_id, phone_number, ProfileName)

    # Save user message to database immediately
    db.save_message(business_id, phone_number, "user", Body)

    # Check if this conversation is in human handoff mode
    if db.is_human_handoff(business_id, phone_number):
        # Check if owner is resuming the bot
        if Body.strip().lower() in ['resume bot', 'resume ai', '/resume']:
            db.set_human_handoff(business_id, phone_number, False)
            await _send_twilio_message(phone_number, "bot is back online! how can i help you?")
        else:
            # Don't respond — human is handling this
            logger.info(f"🙋 Skipping AI response for {phone_number} (human handoff active)")
        resp = MessagingResponse()
        return PlainTextResponse(str(resp), media_type="application/xml")

    # Check if customer is asking for a human
    handoff_triggers = ['talk to someone', 'speak to someone', 'talk to a human', 'speak to a human', 'real person', 'i want a human', 'talk to a person', 'speak to a person', 'customer service', 'talk to owner', 'speak to owner', 'human agent']
    if any(trigger in Body.lower() for trigger in handoff_triggers):
        db.set_human_handoff(business_id, phone_number, True)
        await _send_twilio_message(phone_number, "no problem! i've notified the boss. someone will get back to you shortly. thanks for your patience 🙏")
        resp = MessagingResponse()
        return PlainTextResponse(str(resp), media_type="application/xml")

    # Launch background task to generate AI response and send via Twilio REST API
    asyncio.create_task(_process_and_reply_twilio(business_id, phone_number, Body, ProfileName))

    # Respond INSTANTLY with empty TwiML so Twilio doesn't time out
    resp = MessagingResponse()
    return PlainTextResponse(str(resp), media_type="application/xml")


async def _send_twilio_message(phone_number: str, message: str, media_url: str = None):
    """Send a message via Twilio REST API, optionally with media/image attachments."""
    twilio_api_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    
    data = {
        "From": TWILIO_WHATSAPP_NUMBER,
        "To": f"whatsapp:{phone_number}",
        "Body": message
    }
    
    if media_url:
        data["MediaUrl"] = media_url
        
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            twilio_api_url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data=data
        )
        if response.status_code != 201:
            logger.error(f"❌ Twilio REST API failed to send: {response.text}")


async def _process_and_reply_twilio(business_id: str, phone_number: str, user_message: str, profile_name: str = None):
    """Background task: generate AI response, detect orders, then send via Twilio REST API."""
    try:
        # Simulate human typing delay (7 seconds)
        await asyncio.sleep(7)

        # Generate AI response
        ai_response = await ai_engine.generate_response(
            business_id=business_id,
            phone_number=phone_number,
            user_message=user_message,
            save_user_message=False
        )

        if not ai_response:
            ai_response = "sorry, something went wrong on my end. please try again"

        # Check for AI-triggered handoff
        if "[HANDOFF_TRIGGERED]" in ai_response:
            ai_response = ai_response.replace("[HANDOFF_TRIGGERED]", "").strip()
            db.set_human_handoff(business_id, phone_number, True)
            logger.info(f"🙋 AI triggered human handoff for {phone_number}")

        # Detect if AI is sending payment details (order confirmation)
        business_config = db.get_business_config(business_id)
        payment_info = business_config.get("payment_info", "")
        
        # Default fallback payment detection keywords
        payment_keywords = ["bank", "transfer", "opay", "account", "payment", "pay", "8137048851"]
        if payment_info:
            payment_keywords.extend([w.lower() for w in payment_info.split() if len(w) > 3])
            
        if any(keyword in ai_response.lower() for keyword in payment_keywords) and ("account" in ai_response.lower() or "number" in ai_response.lower() or "pay" in ai_response.lower() or "transfer" in ai_response.lower()):
            # Try to extract order info from conversation
            try:
                customer_name = profile_name or "Unknown"
                order_details = await extract_order_details_via_llm(business_id, phone_number, user_message)
                db.save_order(
                    business_id=business_id,
                    phone_number=phone_number,
                    customer_name=customer_name,
                    items=order_details["items"],
                    total_amount=order_details["total_amount"],
                    delivery_address=order_details["delivery_address"]
                )
                logger.info(f"📦 Order auto-detected and extracted for {phone_number}: {order_details}")
            except Exception as e:
                logger.error(f"Error saving order: {e}")

        # Extract [IMAGE:product_id] tokens (Symmetrical to Meta webhook)
        image_tokens = re.findall(r'\[IMAGE:([a-zA-Z0-9\-]+)\]', ai_response)
        
        # Strip image tokens from text response
        clean_response = re.sub(r'\[IMAGE:[a-zA-Z0-9\-]+\]', '', ai_response).strip()

        # Send clean text response first
        if clean_response:
            await _send_twilio_message(phone_number, clean_response)
            logger.info(f"✅ Twilio text reply sent to {phone_number}")

        # Send images for each token
        for prod_id in image_tokens:
            product = db.get_product_by_id(prod_id)
            if product and product.get("image_url"):
                # Parse multiple images if stored as a JSON array string
                images_to_send = []
                raw_url = product["image_url"]
                if raw_url.startswith("[") and raw_url.endswith("]"):
                    try:
                        import json
                        images_to_send = json.loads(raw_url)
                    except Exception:
                        images_to_send = [raw_url]
                else:
                    images_to_send = [raw_url]
                
                # Filter out empty URLs
                images_to_send = [u for u in images_to_send if u]
                
                base_caption = f"{product['name']}"
                if product.get('price'):
                    try:
                        price_val = float(product['price'])
                        base_caption += f" — ₦{price_val:,.0f}"
                    except Exception:
                        base_caption += f" — ₦{product['price']}"
                
                # Send all the product images via Twilio REST API
                for i, img_url in enumerate(images_to_send):
                    img_caption = f"{base_caption} (Photo {i+1}/{len(images_to_send)})" if len(images_to_send) > 1 else base_caption
                    await _send_twilio_message(phone_number, img_caption, img_url)
                logger.info(f"🖼️ Sent {len(images_to_send)} product image(s) for {prod_id} to {phone_number} via Twilio")

    except Exception as e:
        logger.error(f"❌ Background Twilio reply error: {str(e)}")



# =============================================================================
# HEALTH & UTILITY ENDPOINTS
# =============================================================================

@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    """Root endpoint - Health check and welcome message."""
    return {
        "status": "online",
        "service": "WhatsApp AI Sales Agent",
        "version": "2.0.0",
        "message": "🚀 Your AI Sales Agent is running!"
    }


class SettingsUpdate(BaseModel):
    bot_mode: str
    business_name: str
    business_id: Optional[str] = None

@app.get("/settings")
@limiter.limit("30/minute")
async def get_settings(request: Request, business_id: Optional[str] = Query(None)):
    """Get the current bot mode and business settings."""
    if business_id:
        return db.get_business_config(business_id)
    return db.get_settings()

@app.post("/settings")
@limiter.limit("10/minute")
async def update_settings(request: Request, settings: SettingsUpdate):
    """Update the bot mode and business name."""
    if settings.business_id:
        # Update specific business bot mode
        try:
            res = db.client.table("businesses").update({
                "bot_mode": settings.bot_mode,
                "name": settings.business_name
            }).eq("id", settings.business_id).execute()
            if len(res.data) > 0:
                return {"status": "success", "message": "Business settings updated"}
        except Exception as e:
            logger.error(f"Error updating business settings: {e}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to update business settings"})
    
    success = db.update_settings(settings.bot_mode, settings.business_name)
    if success:
        return {"status": "success", "message": "Settings updated"}
    return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to update settings"})

@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request, business_id: Optional[str] = Query(None)):
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "ai_engine": "active",
        "active_conversations": ai_engine.get_conversation_count(business_id)
    }


@app.get("/stats")
@limiter.limit("30/minute")
async def get_stats(request: Request, business_id: Optional[str] = Query(None)):
    """Get comprehensive application statistics scoped to a business_id."""
    stats = db.get_stats(business_id)
    stats["active_conversations"] = ai_engine.get_conversation_count(business_id)
    stats["whatsapp_configured"] = False
    
    if business_id:
        creds = db.get_business_credentials(business_id)
        stats["whatsapp_configured"] = bool(creds.get("meta_access_token") and creds.get("meta_phone_number_id"))
    else:
        stats["whatsapp_configured"] = bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)
        
    revenue = db.get_revenue_stats(business_id)
    stats.update(revenue)
    handoffs = db.get_handoff_contacts(business_id)
    stats["pending_handoffs"] = len(handoffs)
    return stats


@app.get("/stats/daily")
async def get_daily_stats(business_id: str = Query(...)):
    """Get 7-day daily lead registration and message frequency stats."""
    return db.get_daily_analytics(business_id)


class DemoChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


@app.post("/demo/chat")
@limiter.limit("10/minute")
async def handle_demo_chat(request: Request, req: DemoChatRequest):
    """Handle public landing page demo chat using the AI Engine."""
    if not req.message:
        raise HTTPException(status_code=400, detail="Message is required")
    reply = await ai_engine.generate_demo_response(req.message, req.history)
    return {"reply": reply}


class ManualMessageRequest(BaseModel):
    business_id: str
    phone_number: str
    message: str


@app.post("/chats/send")
@limiter.limit("20/minute")
async def send_manual_message(request: Request, req: ManualMessageRequest):
    """Manually send a message to a WhatsApp lead, logging it to database history."""
    if not req.business_id or not req.phone_number or not req.message:
        raise HTTPException(status_code=400, detail="Missing required parameters")
        
    # 1. Log manual message to local database history
    db.save_message(req.business_id, req.phone_number, "model", req.message)
    
    # 2. Check business WhatsApp provider and credentials
    creds = db.get_business_credentials(req.business_id)
    provider = creds.get("whatsapp_provider", "meta")
    
    success = False
    
    # Route via Evolution API if provider is 'evolution'
    if provider == "evolution":
        instance_name = creds.get("evolution_instance_name")
        apikey = creds.get("evolution_apikey")
        if instance_name and apikey:
            try:
                success = await send_evolution_message(
                    instance_name=instance_name,
                    apikey=apikey,
                    recipient_phone=req.phone_number,
                    message_text=req.message
                )
                if success:
                    logger.info(f"Manual message sent to {req.phone_number} via Evolution API")
            except Exception as e:
                logger.error(f"Failed to send manual message via Evolution: {e}")
    else:
        # Try sending via WhatsApp Meta API if credentials exist
        access_token = creds.get("meta_access_token")
        phone_number_id = creds.get("meta_phone_number_id")
        if access_token and phone_number_id:
            try:
                success = await send_whatsapp_message(
                    recipient_phone=req.phone_number,
                    message_text=req.message,
                    access_token=access_token,
                    phone_number_id=phone_number_id
                )
                if success:
                    logger.info(f"Manual message sent to {req.phone_number} via Meta Graph API")
            except Exception as e:
                logger.error(f"Failed to send manual message via Meta: {e}")
            
    # Fallback to Twilio sandbox if nothing else worked
    if not success:
        try:
            await _send_twilio_message(req.phone_number, req.message)
            success = True
            logger.info(f"Manual message sent to {req.phone_number} via Twilio sandbox fallback")
        except Exception as e:
            logger.error(f"Failed to send manual message via Twilio fallback: {e}")
            
    if success:
        return {"status": "success", "message": "Message sent and logged successfully"}
    else:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Failed to deliver manual message via WhatsApp"}
        )


class TriggerAIRequest(BaseModel):
    business_id: str


@app.post("/chats/{phone}/trigger-ai")
@limiter.limit("20/minute")
async def trigger_ai_response(phone: str, req: TriggerAIRequest, request: Request):
    """
    Manually trigger an AI response for a specific contact conversation.
    Generates response immediately, saves it, sends it via WhatsApp, and returns it.
    """
    if not req.business_id or not phone:
        raise HTTPException(status_code=400, detail="Missing required parameters")
        
    # Get last user message from conversation history
    history = db.get_conversation_history(req.business_id, phone, limit=5)
    user_messages = [msg["parts"][0] for msg in history if msg.get("role") == "user" and msg.get("parts")]
    
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user messages found in history to reply to")
        
    last_user_message = user_messages[-1]
    
    # Generate response via AI Engine immediately (passing save_user_message=False since it's already in history)
    ai_response = await ai_engine.generate_response(
        business_id=req.business_id,
        phone_number=phone,
        user_message=last_user_message,
        save_user_message=False
    )
    
    if not ai_response:
        raise HTTPException(status_code=500, detail="AI engine failed to generate response")
        
    # Check for AI-triggered handoff
    if "[HANDOFF_TRIGGERED]" in ai_response:
        ai_response = ai_response.replace("[HANDOFF_TRIGGERED]", "").strip()
        db.set_human_handoff(req.business_id, phone, True)
        logger.info(f"🙋 AI triggered human handoff during manual trigger for {phone}")
        
    # Send the response via WhatsApp
    creds = db.get_business_credentials(req.business_id)
    provider = creds.get("whatsapp_provider", "meta")
    
    success = False
    
    if provider == "evolution":
        instance_name = creds.get("evolution_instance_name")
        apikey = creds.get("evolution_apikey")
        if instance_name and apikey:
            try:
                success = await send_evolution_message(
                    instance_name=instance_name,
                    apikey=apikey,
                    recipient_phone=phone,
                    message_text=ai_response
                )
            except Exception as e:
                logger.error(f"Failed to send manually triggered AI response via Evolution: {e}")
    else:
        access_token = creds.get("meta_access_token")
        phone_number_id = creds.get("meta_phone_number_id")
        if access_token and phone_number_id:
            try:
                success = await send_whatsapp_message(
                    recipient_phone=phone,
                    message_text=ai_response,
                    access_token=access_token,
                    phone_number_id=phone_number_id
                )
            except Exception as e:
                logger.error(f"Failed to send manually triggered AI response via Meta: {e}")
                
    # Fallback to Twilio sandbox if nothing else worked
    if not success:
        try:
            await _send_twilio_message(phone, ai_response)
            success = True
        except Exception as e:
            logger.error(f"Failed to send manually triggered AI response via Twilio fallback: {e}")
            
    # Note: ai_engine.generate_response already saved the AI response (role: model) to the db!
    
    if success:
        return {"status": "success", "reply": ai_response}
    else:
        raise HTTPException(status_code=500, detail="Failed to deliver AI response via WhatsApp")


@app.get("/contacts")
@limiter.limit("30/minute")
async def get_contacts(request: Request, business_id: Optional[str] = Query(None)):
    """Get all tracked contacts/leads scoped to a business_id."""
    return {
        "contacts": db.get_all_contacts(business_id),
        "total": db.get_stats(business_id)["total_contacts"]
    }


@app.get("/chats")
@limiter.limit("30/minute")
async def get_chats(request: Request, business_id: Optional[str] = Query(None), phone: str = None):
    """Get full chat messages scoped to a business_id."""
    if phone:
        history = db.get_conversation_history(business_id, phone, limit=100)
        return {
            "phone_number": phone,
            "messages": [
                {"role": h["role"], "content": h["parts"][0]} for h in history
            ]
        }
    contacts = db.get_all_contacts(business_id)
    chats = []
    for contact in contacts:
        history = db.get_conversation_history(business_id, contact["phone_number"], limit=100)
        chats.append({
            "phone_number": contact["phone_number"],
            "name": contact.get("name"),
            "message_count": contact.get("message_count", 0),
            "messages": [
                {"role": h["role"], "content": h["parts"][0]} for h in history
            ]
        })
    return {"chats": chats}

class BroadcastRequest(BaseModel):
    message: str
    business_id: str
    phones: Optional[list] = None

@app.post("/broadcast")
@limiter.limit("5/minute")
async def send_broadcast(request: Request, body: BroadcastRequest):
    """Send a promotional/broadcast message to all or selected contacts scoped to a business."""
    contacts = db.get_all_contacts(body.business_id)
    
    # Filter if specific phones were provided
    if body.phones is not None and len(body.phones) > 0:
        contacts = [c for c in contacts if c["phone_number"] in body.phones]
        
    creds = db.get_business_credentials(body.business_id)
    access_token = creds.get("meta_access_token")
    phone_number_id = creds.get("meta_phone_number_id")
    
    success_count = 0
    fail_count = 0
    
    for contact in contacts:
        phone = contact["phone_number"]
        try:
            # Symmetrically try sending via Meta per-business credentials
            success = await send_whatsapp_message(
                recipient_phone=phone,
                message_text=body.message,
                access_token=access_token,
                phone_number_id=phone_number_id
            )
            if success:
                success_count += 1
            else:
                raise Exception("Meta API failed to send")
        except Exception as e:
            logger.error(f"Failed to broadcast to {phone} via Meta API, falling back to Twilio: {str(e)}")
            try:
                # Fallback to sandbox Twilio for testing
                await _send_twilio_message(phone, body.message)
                success_count += 1
            except Exception as t_err:
                logger.error(f"Twilio broadcast fallback also failed for {phone}: {str(t_err)}")
                fail_count += 1
            
    return {"status": "success", "sent": success_count, "failed": fail_count}


@app.delete("/chats/{phone}/clear")
@limiter.limit("10/minute")
async def clear_chat(request: Request, phone: str, business_id: Optional[str] = Query(None)):
    """Clear conversation history for a specific phone number scoped to a business_id."""
    cleared = db.clear_conversation(business_id, phone)
    return {"cleared": cleared, "phone_number": phone}


@app.get("/orders")
@limiter.limit("30/minute")
async def get_orders(request: Request, business_id: Optional[str] = Query(None)):
    """Get all orders scoped to a business_id."""
    return {
        "orders": db.get_all_orders(business_id),
        "stats": db.get_revenue_stats(business_id)
    }


@app.put("/orders/{order_id}/status")
@limiter.limit("20/minute")
async def update_order(request: Request, order_id: int, status: str = Query(...)):
    """Update order status. Valid: pending, paid, dispatched, delivered, cancelled"""
    updated = db.update_order_status(order_id, status)
    return {"updated": updated, "order_id": order_id, "new_status": status}


@app.get("/handoffs")
@limiter.limit("30/minute")
async def get_handoffs(request: Request, business_id: Optional[str] = Query(None)):
    """Get all conversations waiting for human takeover scoped to a business_id."""
    return {"handoffs": db.get_handoff_contacts(business_id)}


@app.post("/handoffs/{phone}/resume")
@limiter.limit("20/minute")
async def resume_bot(request: Request, phone: str, business_id: Optional[str] = Query(None)):
    """Resume AI bot for a conversation after human takeover scoped to a business_id."""
    db.set_human_handoff(business_id, phone, False)
    return {"resumed": True, "phone_number": phone}


@app.post("/handoffs/{phone}/takeover")
@limiter.limit("20/minute")
async def takeover_chat(request: Request, phone: str, business_id: Optional[str] = Query(None)):
    """Take over conversation manually (sets human_handoff = True) scoped to a business_id."""
    db.set_human_handoff(business_id, phone, True)
    return {"takeover": True, "phone_number": phone}


# =============================================================================
# PRODUCT CATALOG ENDPOINTS
# =============================================================================

class ProductCreate(BaseModel):
    business_id: str
    name: str
    description: Optional[str] = ""
    price: Optional[str] = ""
    image_url: Optional[str] = ""
    category: Optional[str] = ""

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None


@app.get("/products")
@limiter.limit("30/minute")
async def get_products(request: Request, business_id: str = Query(...)):
    """Get all products/property listings for a business."""
    products = db.get_products(business_id)
    return {"products": products, "total": len(products)}


@app.post("/products")
@limiter.limit("20/minute")
async def add_product(request: Request, product: ProductCreate):
    """Add a new product/property listing with optional image URL."""
    product_id = db.add_product(
        business_id=product.business_id,
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=product.image_url,
        category=product.category
    )
    if product_id:
        return {"status": "success", "product_id": product_id, "message": f"Product '{product.name}' added successfully"}
    return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to add product"})


@app.put("/products/{product_id}")
@limiter.limit("20/minute")
async def update_product(request: Request, product_id: str, product: ProductUpdate):
    """Update an existing product/property listing."""
    update_data = product.dict(exclude_none=True)
    if not update_data:
        return JSONResponse(status_code=400, content={"status": "error", "message": "No fields to update"})
    
    success = db.update_product(product_id, **update_data)
    if success:
        return {"status": "success", "message": "Product updated successfully"}
    return JSONResponse(status_code=404, content={"status": "error", "message": "Product not found or update failed"})


@app.delete("/products/{product_id}")
@limiter.limit("10/minute")
async def delete_product(request: Request, product_id: str):
    """Delete a product/property listing."""
    success = db.delete_product(product_id)
    if success:
        return {"status": "success", "message": "Product deleted successfully"}
    return JSONResponse(status_code=404, content={"status": "error", "message": "Product not found or delete failed"})


@app.put("/products/{product_id}/toggle")
@limiter.limit("20/minute")
async def toggle_product_availability(request: Request, product_id: str):
    """Toggle a product's availability (show/hide from AI catalog)."""
    product = db.get_product_by_id(product_id)
    if not product:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Product not found"})
    
    new_status = not product.get("is_available", True)
    success = db.update_product(product_id, is_available=new_status)
    if success:
        return {"status": "success", "is_available": new_status, "message": f"Product {'shown' if new_status else 'hidden'} from AI catalog"}
    return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to toggle product"})


@app.post("/products/upload-image")
@limiter.limit("10/minute")
async def upload_product_image(
    request: Request,
    business_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload a product/property image securely to Supabase Storage using the service role key.
    This bypasses client-side RLS policies and resolves the RLS policy error.
    """
    if not db.client:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Database not initialized"})
    
    try:
        # Read file contents
        contents = await file.read()
        
        # Build file path
        # format: {business_id}/{timestamp}_{filename}
        import time
        timestamp = int(time.time() * 1000)
        clean_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', file.filename)
        file_path = f"{business_id}/{timestamp}_{clean_filename}"
        
        # Upload securely via python client (which uses the secret service role key)
        db.client.storage.from_("product-images").upload(
            path=file_path,
            file=contents,
            file_options={"content-type": file.content_type}
        )
        
        # Get public url (which returns a direct string)
        public_url = db.client.storage.from_("product-images").get_public_url(file_path)
        
        logger.info(f"✅ Securely uploaded product image for business {business_id}: {public_url}")
        return {"status": "success", "public_url": public_url}
        
    except Exception as e:
        logger.error(f"❌ Secure image upload failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Upload failed: {str(e)}"})


# =============================================================================
# EVOLUTION API — QR CODE WHATSAPP GATEWAY
# =============================================================================

async def send_evolution_message(
    instance_name: str,
    apikey: str,
    recipient_phone: str,
    message_text: str
) -> bool:
    """
    Send a WhatsApp message via Evolution API.
    """
    if not EVOLUTION_API_URL:
        logger.error("EVOLUTION_API_URL is not configured!")
        return False
        
    url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
    headers = {
        "apikey": apikey,
        "Content-Type": "application/json"
    }
    payload = {
        "number": recipient_phone,
        "text": message_text
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code in (200, 201):
                logger.info(f"Evolution message sent to {recipient_phone}")
                return True
            else:
                logger.error(f"Evolution send failed. Status: {response.status_code}, Body: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error sending Evolution message: {e}")
        return False


async def _process_and_reply_evolution(business_id: str, phone_number: str, message_body: str, sender_name: str = None):
    """Background task: generate AI response, then send via Evolution API."""
    try:
        # Simulate human typing delay
        await asyncio.sleep(7)
        
        # Get business credentials
        creds = db.get_business_credentials(business_id)
        instance_name = creds.get("evolution_instance_name")
        apikey = creds.get("evolution_apikey")
        
        if not instance_name or not apikey:
            logger.error(f"Evolution credentials missing for business {business_id}")
            return
        
        # Generate AI response
        ai_response = await ai_engine.generate_response(
            business_id=business_id,
            phone_number=phone_number,
            user_message=message_body,
            save_user_message=False
        )
        
        if ai_response:
            # Check for AI-triggered handoff
            if "[HANDOFF_TRIGGERED]" in ai_response:
                ai_response = ai_response.replace("[HANDOFF_TRIGGERED]", "").strip()
                db.set_human_handoff(business_id, phone_number, True)
                logger.info(f"AI triggered human handoff for {phone_number}")

            # Dynamic Order Detection
            business_config = db.get_business_config(business_id)
            payment_info = business_config.get("payment_info", "")
            payment_keywords = ["bank", "transfer", "opay", "account", "payment", "pay"]
            if payment_info:
                payment_keywords.extend([w.lower() for w in payment_info.split() if len(w) > 3])
                
            if any(keyword in ai_response.lower() for keyword in payment_keywords) and (
                "account" in ai_response.lower() or "number" in ai_response.lower() or 
                "pay" in ai_response.lower() or "transfer" in ai_response.lower()
            ):
                try:
                    customer_name = sender_name if sender_name else "Unknown"
                    order_details = await extract_order_details_via_llm(business_id, phone_number, message_body)
                    db.save_order(
                        business_id=business_id,
                        phone_number=phone_number,
                        customer_name=customer_name,
                        items=order_details["items"],
                        total_amount=order_details["total_amount"],
                        delivery_address=order_details["delivery_address"]
                    )
                    logger.info(f"📦 Order auto-detected and extracted for {phone_number}: {order_details}")
                except Exception as e:
                    logger.error(f"Error saving order: {e}")

            # Extract [IMAGE:product_id] tokens
            image_tokens = re.findall(r'\[IMAGE:([a-zA-Z0-9\-]+)\]', ai_response)
            clean_response = re.sub(r'\[IMAGE:[a-zA-Z0-9\-]+\]', '', ai_response).strip()
            
            # Send clean text response
            if clean_response:
                await send_evolution_message(
                    instance_name=instance_name,
                    apikey=apikey,
                    recipient_phone=phone_number,
                    message_text=clean_response
                )
            
            # Send product images via Evolution API
            for prod_id in image_tokens:
                product = db.get_product_by_id(prod_id)
                if product and product.get("image_url"):
                    images_to_send = []
                    raw_url = product["image_url"]
                    if raw_url.startswith("[") and raw_url.endswith("]"):
                        try:
                            import json
                            images_to_send = json.loads(raw_url)
                        except Exception:
                            images_to_send = [raw_url]
                    else:
                        images_to_send = [raw_url]
                    
                    images_to_send = [u for u in images_to_send if u]
                    base_caption = f"{product['name']}"
                    if product.get('price'):
                        try:
                            price_val = float(product['price'])
                            base_caption += f" — N{price_val:,.0f}"
                        except Exception:
                            base_caption += f" — N{product['price']}"
                    
                    for img_url in images_to_send:
                        # Send image via Evolution API
                        img_payload = {
                            "number": phone_number,
                            "mediatype": "image",
                            "media": img_url,
                            "caption": base_caption
                        }
                        try:
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                await client.post(
                                    f"{EVOLUTION_API_URL}/message/sendMedia/{instance_name}",
                                    headers={"apikey": apikey, "Content-Type": "application/json"},
                                    json=img_payload
                                )
                        except Exception as img_e:
                            logger.error(f"Error sending Evolution image: {img_e}")
        else:
            logger.error("AI engine returned empty response")
            
    except Exception as e:
        logger.error(f"Background Evolution reply error: {e}")


@app.post("/webhook/evolution/{business_id}")
async def handle_evolution_webhook(business_id: str, request: Request) -> JSONResponse:
    """
    Webhook handler for incoming WhatsApp messages via Evolution API.
    Evolution API sends a different JSON format than Meta's webhook.
    """
    try:
        body = await request.json()
        logger.info(f"Evolution webhook received for business {business_id}")
        logger.debug(f"Evolution payload: {body}")
        
        # Evolution API event types: messages.upsert, connection.update, qrcode.updated, etc.
        event = body.get("event", "")
        
        if event == "messages.upsert":
            data = body.get("data", {})
            
            # Only process incoming messages (not outgoing ones)
            key = data.get("key", {})
            if key.get("fromMe", False):
                return JSONResponse(content={"status": "ok"}, status_code=200)
            
            # Extract message content
            remote_jid = key.get("remoteJid", "")
            # Convert WhatsApp JID (e.g., '2349012345678@s.whatsapp.net') to phone number
            phone_number = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid
            
            message_obj = data.get("message", {})
            # Handle text messages
            message_body = (
                message_obj.get("conversation") or
                message_obj.get("extendedTextMessage", {}).get("text") or
                ""
            )
            
            if not message_body:
                return JSONResponse(content={"status": "ok"}, status_code=200)
            
            sender_name = data.get("pushName", "")
            logger.info(f"Evolution message from {phone_number}: {message_body[:50]}...")
            
            # Save contact name
            if sender_name:
                db.update_contact_name(business_id, phone_number, sender_name)
            
            # Ensure contact exists in database
            db.save_message(business_id, phone_number, "user", message_body)
            
            # Check human handoff
            if db.is_human_handoff(business_id, phone_number):
                if message_body.strip().lower() in ['resume bot', 'resume ai', '/resume']:
                    db.set_human_handoff(business_id, phone_number, False)
                    creds = db.get_business_credentials(business_id)
                    await send_evolution_message(
                        instance_name=creds.get("evolution_instance_name", ""),
                        apikey=creds.get("evolution_apikey", ""),
                        recipient_phone=phone_number,
                        message_text="bot is back online! how can i help you?"
                    )
                else:
                    logger.info(f"Skipping AI response for {phone_number} (human handoff active)")
                return JSONResponse(content={"status": "ok"}, status_code=200)

            # Check if customer wants a human
            handoff_triggers = [
                'talk to someone', 'speak to someone', 'talk to a human', 
                'speak to a human', 'real person', 'i want a human', 
                'talk to a person', 'speak to a person', 'customer service', 
                'talk to owner', 'speak to owner', 'human agent'
            ]
            if any(trigger in message_body.lower() for trigger in handoff_triggers):
                db.set_human_handoff(business_id, phone_number, True)
                creds = db.get_business_credentials(business_id)
                await send_evolution_message(
                    instance_name=creds.get("evolution_instance_name", ""),
                    apikey=creds.get("evolution_apikey", ""),
                    recipient_phone=phone_number,
                    message_text="no problem! i've notified the boss. someone will get back to you shortly. thanks for your patience"
                )
                return JSONResponse(content={"status": "ok"}, status_code=200)
            
            # Process AI reply in background task
            asyncio.create_task(_process_and_reply_evolution(
                business_id, phone_number, message_body, sender_name
            ))
        
        elif event == "connection.update":
            state = body.get("data", {}).get("state", "")
            logger.info(f"Evolution connection update for business {business_id}: {state}")
            if state == "open":
                # Mark webhook as connected in database
                db.mark_webhook_verified(business_id)
        
        return JSONResponse(content={"status": "ok"}, status_code=200)
        
    except Exception as e:
        logger.error(f"Error in Evolution webhook: {e}")
        return JSONResponse(content={"status": "ok"}, status_code=200)


@app.post("/evolution/create-instance/{business_id}")
async def create_evolution_instance(business_id: str, request: Request) -> JSONResponse:
    """
    Create a new Evolution API instance for a business and return the QR code.
    Called from the dashboard when a merchant clicks 'Connect via QR Scan'.
    """
    if not EVOLUTION_API_URL or not EVOLUTION_API_GLOBAL_KEY:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Evolution API is not configured on the server."}
        )
    
    try:
        # Generate a unique instance name based on business_id
        instance_name = f"sf_{business_id[:8]}"
        
        # Build the webhook URL for this business
        body_data = await request.json() if request.headers.get("content-type") == "application/json" else {}
        server_url = body_data.get("server_url", os.getenv("RENDER_EXTERNAL_URL", "https://api.salesaiflow.online"))
        webhook_url = f"{server_url}/webhook/evolution/{business_id}"
        
        # Step 1: Create instance on Evolution API
        create_url = f"{EVOLUTION_API_URL}/instance/create"
        headers = {
            "apikey": EVOLUTION_API_GLOBAL_KEY,
            "Content-Type": "application/json"
        }
        create_payload = {
            "instanceName": instance_name,
            "integration": "WHATSAPP-BAILEYS",
            "qrcode": True,
            "webhook": {
                "url": webhook_url,
                "byEvents": False,
                "base64": False,
                "events": [
                    "MESSAGES_UPSERT",
                    "CONNECTION_UPDATE",
                    "QRCODE_UPDATED"
                ]
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(create_url, headers=headers, json=create_payload)
            
            if resp.status_code in (200, 201):
                result = resp.json()
                instance_apikey = result.get("hash", result.get("apikey", EVOLUTION_API_GLOBAL_KEY))
                qr_code = result.get("qrcode", {}).get("base64", "")
                
                # Save credentials to database
                db.save_evolution_credentials(business_id, instance_name, instance_apikey)
                
                return JSONResponse(content={
                    "status": "success",
                    "instance_name": instance_name,
                    "qr_code": qr_code,
                    "webhook_url": webhook_url
                })
            else:
                logger.error(f"Evolution instance creation failed: {resp.status_code} — {resp.text}")
                return JSONResponse(
                    status_code=resp.status_code,
                    content={"status": "error", "message": f"Evolution API error: {resp.text}"}
                )
                
    except Exception as e:
        logger.error(f"Error creating Evolution instance: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.get("/evolution/qrcode/{business_id}")
async def get_evolution_qrcode(business_id: str, request: Request) -> JSONResponse:
    """
    Fetch the current QR code for a business's Evolution instance.
    Used by the dashboard to refresh the QR image.
    """
    if not EVOLUTION_API_URL:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Evolution API not configured"})
    
    try:
        creds = db.get_business_credentials(business_id)
        instance_name = creds.get("evolution_instance_name")
        apikey = creds.get("evolution_apikey", EVOLUTION_API_GLOBAL_KEY)
        
        if not instance_name:
            return JSONResponse(status_code=404, content={"status": "error", "message": "No Evolution instance found for this business"})
        
        # Fetch connection state
        async with httpx.AsyncClient(timeout=15.0) as client:
            state_resp = await client.get(
                f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}",
                headers={"apikey": apikey}
            )
            
            if state_resp.status_code == 200:
                state_data = state_resp.json()
                connection_state = state_data.get("instance", {}).get("state", "close")
                
                if connection_state == "open":
                    return JSONResponse(content={
                        "status": "connected",
                        "state": "open",
                        "qr_code": ""
                    })
            
            # If not connected, fetch QR code
            qr_resp = await client.get(
                f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
                headers={"apikey": apikey}
            )
            
            if qr_resp.status_code == 200:
                qr_data = qr_resp.json()
                qr_base64 = qr_data.get("base64", "")
                return JSONResponse(content={
                    "status": "waiting",
                    "state": "connecting",
                    "qr_code": qr_base64
                })
            else:
                return JSONResponse(
                    status_code=qr_resp.status_code,
                    content={"status": "error", "message": qr_resp.text}
                )
                
    except Exception as e:
        logger.error(f"Error fetching Evolution QR code: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.delete("/evolution/disconnect/{business_id}")
async def disconnect_evolution_instance(business_id: str, request: Request) -> JSONResponse:
    """
    Disconnect and delete a business's Evolution instance.
    """
    if not EVOLUTION_API_URL:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Evolution API not configured"})
    
    try:
        creds = db.get_business_credentials(business_id)
        instance_name = creds.get("evolution_instance_name")
        apikey = creds.get("evolution_apikey", EVOLUTION_API_GLOBAL_KEY)
        
        if not instance_name:
            return JSONResponse(status_code=404, content={"status": "error", "message": "No instance found"})
        
        # Logout and delete instance
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.delete(
                f"{EVOLUTION_API_URL}/instance/logout/{instance_name}",
                headers={"apikey": apikey}
            )
            await client.delete(
                f"{EVOLUTION_API_URL}/instance/delete/{instance_name}",
                headers={"apikey": apikey}
            )
        
        # Clear credentials from database
        db.save_evolution_credentials(business_id, "", "")
        
        return JSONResponse(content={"status": "success", "message": "Instance disconnected"})
        
    except Exception as e:
        logger.error(f"Error disconnecting Evolution instance: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Use PORT environment variable (set by Railway/Render) or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
