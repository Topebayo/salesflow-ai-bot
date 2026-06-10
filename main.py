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

# Add CORS middleware to allow the dashboard to fetch data securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
            user_message=message_body
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
                    db.save_order(
                        business_id=business_id,
                        phone_number=phone_number,
                        customer_name=customer_name,
                        items=message_body,
                        total_amount=0,
                        delivery_address=None
                    )
                    logger.info(f"📦 Order auto-detected for {phone_number}")
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
            user_message=user_message
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
                # Save order with the AI response as items description
                db.save_order(
                    business_id=business_id,
                    phone_number=phone_number,
                    customer_name=customer_name,
                    items=user_message,  # Customer's last message usually contains order
                    total_amount=0,  # Will be updated manually
                    delivery_address=None
                )
                logger.info(f"📦 Order auto-detected for {phone_number}")
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
async def root():
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
async def get_settings(business_id: Optional[str] = Query(None)):
    """Get the current bot mode and business settings."""
    if business_id:
        return db.get_business_config(business_id)
    return db.get_settings()

@app.post("/settings")
async def update_settings(settings: SettingsUpdate):
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
async def health_check(business_id: Optional[str] = Query(None)):
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "ai_engine": "active",
        "active_conversations": ai_engine.get_conversation_count(business_id)
    }


@app.get("/stats")
async def get_stats(business_id: Optional[str] = Query(None)):
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
async def handle_demo_chat(req: DemoChatRequest):
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
async def send_manual_message(req: ManualMessageRequest):
    """Manually send a message to a WhatsApp lead, logging it to database history."""
    if not req.business_id or not req.phone_number or not req.message:
        raise HTTPException(status_code=400, detail="Missing required parameters")
        
    # 1. Log manual message to local database history
    db.save_message(req.business_id, req.phone_number, "model", req.message)
    
    # 2. Check business WhatsApp Graph API credentials
    creds = db.get_business_credentials(req.business_id)
    access_token = creds.get("meta_access_token")
    phone_number_id = creds.get("meta_phone_number_id")
    
    success = False
    
    # Try sending via WhatsApp Meta API first if credentials exist
    if access_token and phone_number_id:
        try:
            success = await send_whatsapp_message(
                recipient_phone=req.phone_number,
                message_text=req.message,
                access_token=access_token,
                phone_number_id=phone_number_id
            )
            if success:
                logger.info(f"✅ Manual message sent to {req.phone_number} via Meta Graph API")
        except Exception as e:
            logger.error(f"Failed to send manual message via Meta: {e}")
            
    # Fallback to Twilio sandbox if Meta credentials are not configured
    if not success:
        try:
            await _send_twilio_message(req.phone_number, req.message)
            success = True
            logger.info(f"✅ Manual message sent to {req.phone_number} via Twilio sandbox fallback")
        except Exception as e:
            logger.error(f"Failed to send manual message via Twilio fallback: {e}")
            
    if success:
        return {"status": "success", "message": "Message sent and logged successfully"}
    else:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Failed to deliver manual message via WhatsApp"}
        )


@app.get("/contacts")
async def get_contacts(business_id: Optional[str] = Query(None)):
    """Get all tracked contacts/leads scoped to a business_id."""
    return {
        "contacts": db.get_all_contacts(business_id),
        "total": db.get_stats(business_id)["total_contacts"]
    }


@app.get("/chats")
async def get_chats(business_id: Optional[str] = Query(None), phone: str = None):
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
async def send_broadcast(request: BroadcastRequest):
    """Send a promotional/broadcast message to all or selected contacts scoped to a business."""
    contacts = db.get_all_contacts(request.business_id)
    
    # Filter if specific phones were provided
    if request.phones is not None and len(request.phones) > 0:
        contacts = [c for c in contacts if c["phone_number"] in request.phones]
        
    creds = db.get_business_credentials(request.business_id)
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
                message_text=request.message,
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
                await _send_twilio_message(phone, request.message)
                success_count += 1
            except Exception as t_err:
                logger.error(f"Twilio broadcast fallback also failed for {phone}: {str(t_err)}")
                fail_count += 1
            
    return {"status": "success", "sent": success_count, "failed": fail_count}


@app.delete("/chats/{phone}/clear")
async def clear_chat(phone: str, business_id: Optional[str] = Query(None)):
    """Clear conversation history for a specific phone number scoped to a business_id."""
    cleared = db.clear_conversation(business_id, phone)
    return {"cleared": cleared, "phone_number": phone}


@app.get("/orders")
async def get_orders(business_id: Optional[str] = Query(None)):
    """Get all orders scoped to a business_id."""
    return {
        "orders": db.get_all_orders(business_id),
        "stats": db.get_revenue_stats(business_id)
    }


@app.put("/orders/{order_id}/status")
async def update_order(order_id: int, status: str = Query(...)):
    """Update order status. Valid: pending, paid, dispatched, delivered, cancelled"""
    updated = db.update_order_status(order_id, status)
    return {"updated": updated, "order_id": order_id, "new_status": status}


@app.get("/handoffs")
async def get_handoffs(business_id: Optional[str] = Query(None)):
    """Get all conversations waiting for human takeover scoped to a business_id."""
    return {"handoffs": db.get_handoff_contacts(business_id)}


@app.post("/handoffs/{phone}/resume")
async def resume_bot(phone: str, business_id: Optional[str] = Query(None)):
    """Resume AI bot for a conversation after human takeover scoped to a business_id."""
    db.set_human_handoff(business_id, phone, False)
    return {"resumed": True, "phone_number": phone}


@app.post("/handoffs/{phone}/takeover")
async def takeover_chat(phone: str, business_id: Optional[str] = Query(None)):
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
async def get_products(business_id: str = Query(...)):
    """Get all products/property listings for a business."""
    products = db.get_products(business_id)
    return {"products": products, "total": len(products)}


@app.post("/products")
async def add_product(product: ProductCreate):
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
async def update_product(product_id: str, product: ProductUpdate):
    """Update an existing product/property listing."""
    update_data = product.dict(exclude_none=True)
    if not update_data:
        return JSONResponse(status_code=400, content={"status": "error", "message": "No fields to update"})
    
    success = db.update_product(product_id, **update_data)
    if success:
        return {"status": "success", "message": "Product updated successfully"}
    return JSONResponse(status_code=404, content={"status": "error", "message": "Product not found or update failed"})


@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Delete a product/property listing."""
    success = db.delete_product(product_id)
    if success:
        return {"status": "success", "message": "Product deleted successfully"}
    return JSONResponse(status_code=404, content={"status": "error", "message": "Product not found or delete failed"})


@app.put("/products/{product_id}/toggle")
async def toggle_product_availability(product_id: str):
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
async def upload_product_image(
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
