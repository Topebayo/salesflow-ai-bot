"""
=============================================================================
WHATSAPP AI SALES AGENT - MAIN APPLICATION
=============================================================================
FastAPI application that handles WhatsApp webhook events and integrates
with the Gemini AI engine to power automated sales conversations.

Author: Your Agency Name
Version: 1.0.0
=============================================================================
"""

import os
import logging
import asyncio
import httpx
from typing import Optional
from contextlib import asynccontextmanager

from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi import FastAPI, Request, HTTPException, Query, Form
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

# Add CORS middleware to allow the dashboard to fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to match your frontend domain
    allow_credentials=True,
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
        Tuple of (phone_number, message_body, message_id) or None if not a valid message
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
        
        if phone_number and message_body:
            return (phone_number, message_body, message_id)
        
        return None
        
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error extracting message data: {str(e)}")
        return None


async def send_whatsapp_message(
    recipient_phone: str,
    message_text: str
) -> bool:
    """
    Send a WhatsApp message via the Meta Graph API.
    
    This function makes an async HTTP POST request to the WhatsApp Business API
    to deliver the AI-generated response back to the user.
    
    Args:
        recipient_phone: The recipient's phone number (in international format without +)
        message_text: The message content to send
        
    Returns:
        True if message was sent successfully, False otherwise
        
    WhatsApp Send Message API Request:
    POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
    Headers:
        Authorization: Bearer {access_token}
        Content-Type: application/json
    Body:
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "{recipient_phone}",
            "type": "text",
            "text": {
                "preview_url": false,
                "body": "{message_text}"
            }
        }
    """
    
    # Validate configuration
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("❌ WhatsApp API credentials not configured!")
        return False
    
    # Prepare the request headers
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Prepare the message payload
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
        # Send the message using async HTTP client
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WHATSAPP_API_URL,
                headers=headers,
                json=payload
            )
            
            # Check response status
            if response.status_code == 200:
                response_data = response.json()
                message_id = response_data.get("messages", [{}])[0].get("id", "unknown")
                logger.info(f"✅ Message sent successfully! ID: {message_id}")
                return True
            else:
                logger.error(f"❌ Failed to send message. Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        logger.error("❌ Timeout while sending WhatsApp message")
        return False
    except httpx.RequestError as e:
        logger.error(f"❌ Request error while sending WhatsApp message: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending WhatsApp message: {str(e)}")
        return False


async def mark_message_as_read(message_id: str) -> bool:
    """
    Mark a received message as read (shows blue ticks to the sender).
    
    Args:
        message_id: The WhatsApp message ID to mark as read
        
    Returns:
        True if successful, False otherwise
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        return False
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
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
                WHATSAPP_API_URL,
                headers=headers,
                json=payload
            )
            return response.status_code == 200
    except Exception as e:
        logger.debug(f"Could not mark message as read: {str(e)}")
        return False


# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@app.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
) -> PlainTextResponse:
    """
    WhatsApp Webhook Verification Endpoint (GET)
    
    When you configure a webhook URL in the Meta Developer Console,
    Meta sends a GET request with verification parameters to confirm
    your endpoint is valid and owned by you.
    
    Verification Request Parameters:
    - hub.mode: Should be "subscribe"
    - hub.verify_token: Your custom token (must match WHATSAPP_VERIFY_TOKEN)
    - hub.challenge: A random string that must be echoed back
    
    If verification succeeds:
    - Return the hub.challenge value as plain text
    
    If verification fails:
    - Return 403 Forbidden
    """
    logger.info("📥 Received webhook verification request")
    logger.info(f"   Mode: {hub_mode}")
    logger.info(f"   Token: {hub_verify_token}")
    logger.info(f"   Challenge: {hub_challenge}")
    
    # Verify the mode and token
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ Webhook verification successful!")
        # Return the challenge to confirm verification
        return PlainTextResponse(content=hub_challenge, status_code=200)
    else:
        logger.warning("❌ Webhook verification failed - token mismatch!")
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def handle_webhook(request: Request) -> JSONResponse:
    """
    WhatsApp Webhook Handler Endpoint (POST)
    
    This endpoint receives all incoming WhatsApp events including:
    - New messages (text, media, location, etc.)
    - Message status updates (sent, delivered, read)
    - Button/interactive responses
    
    Processing Flow:
    1. Parse the incoming JSON payload
    2. Extract the sender's phone number and message content
    3. Generate an AI response using the Gemini engine
    4. Send the response back via WhatsApp API
    5. Return 200 OK to acknowledge receipt (IMPORTANT: Meta expects this quickly)
    """
    try:
        # Parse the incoming JSON payload
        body = await request.json()
        
        # Log the incoming request (be careful with this in production for privacy)
        logger.info("📨 Received webhook event")
        logger.debug(f"Payload: {body}")
        
        # Extract message data from the payload
        message_data = extract_message_data(body)
        
        if message_data:
            phone_number, message_body, message_id = message_data
            
            logger.info(f"📱 Message from {phone_number}: {message_body[:50]}...")
            
            # Try to extract and save the sender's name from the payload
            try:
                contacts = body["entry"][0]["changes"][0]["value"].get("contacts", [])
                if contacts:
                    sender_name = contacts[0].get("profile", {}).get("name", "")
                    if sender_name:
                        db.update_contact_name(phone_number, sender_name)
            except (KeyError, IndexError):
                pass
            
            # Mark the message as read (optional but improves UX)
            await mark_message_as_read(message_id)
            
            # Generate AI response using Gemini
            ai_response = await ai_engine.generate_response(
                phone_number=phone_number,
                user_message=message_body
            )
            
            if ai_response:
                # Send the AI response back to the user
                success = await send_whatsapp_message(
                    recipient_phone=phone_number,
                    message_text=ai_response
                )
                
                if success:
                    logger.info(f"✅ Response sent to {phone_number}")
                else:
                    logger.error(f"❌ Failed to send response to {phone_number}")
            else:
                logger.error("❌ AI engine returned empty response")
        
        else:
            # This might be a status update or other event type
            logger.debug("ℹ️ Non-message event received (status update, etc.)")
        
        # ALWAYS return 200 OK to acknowledge receipt
        # Meta will retry if they don't receive a 200 response
        return JSONResponse(content={"status": "ok"}, status_code=200)
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        # STILL RETURN 200 TO PREVENT META FROM RETRYING
        # LOG THE ERROR FOR DEBUGGING BUT DON'T EXPOSE IT
        return JSONResponse(content={"status": "ok"}, status_code=200)

@app.post("/twilio/webhook")
async def handle_twilio_webhook(
    From: str = Form(...),
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
    logger.info(f"📨 Received Twilio message from {phone_number}: {Body[:50]}...")

    # Save contact name if provided
    if ProfileName:
        db.update_contact_name(phone_number, ProfileName)

    # Launch background task to generate AI response and send via Twilio REST API
    asyncio.create_task(_process_and_reply_twilio(phone_number, Body))

    # Respond INSTANTLY with empty TwiML so Twilio doesn't time out
    resp = MessagingResponse()
    return PlainTextResponse(str(resp), media_type="application/xml")


async def _process_and_reply_twilio(phone_number: str, user_message: str):
    """Background task: generate AI response then send it via Twilio REST API."""
    try:
        # Generate AI response
        ai_response = await ai_engine.generate_response(
            phone_number=phone_number,
            user_message=user_message
        )

        if not ai_response:
            ai_response = "sorry, something went wrong on my end. please try again"

        # Send the response via Twilio REST API
        twilio_api_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                twilio_api_url,
                auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                data={
                    "From": TWILIO_WHATSAPP_NUMBER,
                    "To": f"whatsapp:{phone_number}",
                    "Body": ai_response
                }
            )

            if response.status_code == 201:
                logger.info(f"✅ Twilio reply sent to {phone_number}")
            else:
                logger.error(f"❌ Twilio send failed: {response.status_code} {response.text}")

    except Exception as e:
        logger.error(f"❌ Background Twilio reply error: {str(e)}")



# =============================================================================
# HEALTH & UTILITY ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - Health check and welcome message.
    """
    return {
        "status": "online",
        "service": "WhatsApp AI Sales Agent",
        "version": "1.0.0",
        "message": "🚀 Your AI Sales Agent is running! Configure your webhook URL in Meta Developer Console.",
        "endpoints": {
            "webhook": "/webhook (GET for verification, POST for messages)",
            "health": "/health",
            "stats": "/stats"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "ai_engine": "active",
        "active_conversations": ai_engine.get_conversation_count()
    }


@app.get("/stats")
async def get_stats():
    """
    Get comprehensive application statistics from the database.
    Includes total contacts, messages, today's activity, and top contacts.
    """
    stats = db.get_stats()
    stats["active_conversations"] = ai_engine.get_conversation_count()
    stats["whatsapp_configured"] = bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)
    return stats


@app.get("/contacts")
async def get_contacts():
    """
    Get all tracked contacts/leads with their message history stats.
    Useful for lead management and follow-up.
    """
    return {
        "contacts": db.get_all_contacts(),
        "total": db.get_stats()["total_contacts"]
    }


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
