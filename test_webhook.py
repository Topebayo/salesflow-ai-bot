"""
=============================================================================
END-TO-END DIAGNOSTIC TEST
=============================================================================
Tests each step of the message pipeline to find where it breaks:
1. AI Engine generates response
2. WhatsApp API accepts the message
"""

import asyncio
import sys
import os
import httpx
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Colors for terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def header(text):
    print(f"\n{CYAN}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{RESET}\n")

def ok(text):
    print(f"  {GREEN}✅ {text}{RESET}")

def fail(text):
    print(f"  {RED}❌ {text}{RESET}")

def warn(text):
    print(f"  {YELLOW}⚠️  {text}{RESET}")

def info(text):
    print(f"  {CYAN}ℹ️  {text}{RESET}")


async def run_diagnostics():
    header("WHATSAPP AI SALES AGENT - DIAGNOSTIC TEST")
    
    # =========================================================================
    # TEST 1: Environment Variables
    # =========================================================================
    print(f"{YELLOW}TEST 1: Checking Environment Variables{RESET}")
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    wa_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    wa_verify = os.getenv("WHATSAPP_VERIFY_TOKEN")
    wa_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    all_env_ok = True
    
    if gemini_key:
        ok(f"GEMINI_API_KEY: {gemini_key[:10]}...{gemini_key[-5:]}")
    else:
        fail("GEMINI_API_KEY: NOT SET")
        all_env_ok = False
    
    if wa_token:
        ok(f"WHATSAPP_ACCESS_TOKEN: {wa_token[:15]}...{wa_token[-10:]}")
    else:
        fail("WHATSAPP_ACCESS_TOKEN: NOT SET")
        all_env_ok = False
    
    if wa_verify:
        ok(f"WHATSAPP_VERIFY_TOKEN: {wa_verify}")
    else:
        fail("WHATSAPP_VERIFY_TOKEN: NOT SET")
        all_env_ok = False
    
    if wa_phone_id:
        ok(f"WHATSAPP_PHONE_NUMBER_ID: {wa_phone_id}")
    else:
        fail("WHATSAPP_PHONE_NUMBER_ID: NOT SET")
        all_env_ok = False
    
    if not all_env_ok:
        fail("Fix missing environment variables before continuing!")
        return
    
    # =========================================================================
    # TEST 2: AI Engine Response
    # =========================================================================
    print(f"\n{YELLOW}TEST 2: Testing AI Engine (Gemini){RESET}")
    
    try:
        from ai_engine import ai_engine
        ok("AI Engine imported successfully")
        
        response = await ai_engine.generate_response(
            phone_number="+2340000000000",
            user_message="Hello, I'm interested in your services"
        )
        
        if response:
            ok(f"AI Generated Response ({len(response)} chars):")
            print(f"  {CYAN}---")
            # Print first 200 chars
            for line in response[:300].split('\n'):
                print(f"  {line}")
            if len(response) > 300:
                print(f"  ... (truncated)")
            print(f"  ---{RESET}")
        else:
            fail("AI Engine returned empty response!")
            return
            
        # Clear test conversation
        ai_engine.clear_conversation("+2340000000000")
        
    except Exception as e:
        fail(f"AI Engine error: {str(e)}")
        return
    
    # =========================================================================
    # TEST 3: WhatsApp API Token Validation
    # =========================================================================
    print(f"\n{YELLOW}TEST 3: Testing WhatsApp API Token{RESET}")
    
    wa_api_url = f"https://graph.facebook.com/v18.0/{wa_phone_id}/messages"
    info(f"API URL: {wa_api_url}")
    
    headers = {
        "Authorization": f"Bearer {wa_token}",
        "Content-Type": "application/json"
    }
    
    # First, let's just check if the token is valid by calling a simple endpoint
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Check token validity using the debug_token endpoint won't work,
            # so let's check the phone number ID endpoint
            check_url = f"https://graph.facebook.com/v18.0/{wa_phone_id}"
            check_response = await client.get(
                check_url,
                headers={"Authorization": f"Bearer {wa_token}"}
            )
            
            if check_response.status_code == 200:
                phone_data = check_response.json()
                ok(f"WhatsApp API Token is VALID")
                ok(f"Phone Number: {phone_data.get('display_phone_number', 'N/A')}")
                ok(f"Verified Name: {phone_data.get('verified_name', 'N/A')}")
                ok(f"Quality Rating: {phone_data.get('quality_rating', 'N/A')}")
            else:
                fail(f"WhatsApp API Token CHECK FAILED! Status: {check_response.status_code}")
                error_data = check_response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                error_code = error_data.get("error", {}).get("code", "N/A")
                fail(f"Error Code: {error_code}")
                fail(f"Error Message: {error_msg}")
                
                if "expired" in error_msg.lower() or error_code == 190:
                    warn("YOUR ACCESS TOKEN HAS EXPIRED!")
                    warn("Go to https://developers.facebook.com/apps/")
                    warn("Navigate to: Your App > WhatsApp > API Setup")
                    warn("Generate a new temporary access token (valid for 24 hours)")
                    warn("Or create a System User token for a permanent one")
                elif "invalid" in error_msg.lower():
                    warn("YOUR ACCESS TOKEN IS INVALID!")
                    warn("Double-check your token in the .env file")
                
                return
                
    except httpx.TimeoutException:
        fail("Timeout connecting to Meta API - check your internet connection")
        return
    except Exception as e:
        fail(f"Error checking token: {str(e)}")
        return
    
    # =========================================================================
    # TEST 4: Send a Test Message
    # =========================================================================
    print(f"\n{YELLOW}TEST 4: Sending Test Message via WhatsApp API{RESET}")
    
    # Use command-line argument or skip
    your_phone = sys.argv[1] if len(sys.argv) > 1 else ""
    
    if not your_phone:
        info("To send a test message, run: python test_webhook.py YOUR_PHONE_NUMBER")
    
    if not your_phone:
        warn("No phone number provided, skipping send test")
    else:
        test_message = "🤖 Test from your AI Sales Agent!\n\nIf you see this message, your WhatsApp integration is working perfectly! ✅"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": your_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": test_message
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    wa_api_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    resp_data = response.json()
                    msg_id = resp_data.get("messages", [{}])[0].get("id", "unknown")
                    ok(f"Message SENT successfully!")
                    ok(f"Message ID: {msg_id}")
                    ok(f"Check your WhatsApp - you should receive the test message!")
                else:
                    fail(f"Failed to send! Status: {response.status_code}")
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown")
                    error_code = error_data.get("error", {}).get("code", "N/A")
                    fail(f"Error Code: {error_code}")
                    fail(f"Error: {error_msg}")
                    
                    # Common error explanations
                    if error_code == 131030:
                        warn("The recipient phone number is not a valid WhatsApp number")
                    elif error_code == 131026:
                        warn("Message failed: The recipient hasn't opted in or the number is incorrect")
                    elif "template" in error_msg.lower() or error_code == 131047:
                        warn("You need to use a MESSAGE TEMPLATE for first-time messages!")
                        warn("The user must message YOU first, or you must use an approved template")
                        warn("Try messaging your business number from WhatsApp first, then run this test again")
                        
        except Exception as e:
            fail(f"Send error: {str(e)}")
    
    # =========================================================================
    # TEST 5: Local Server Check
    # =========================================================================
    print(f"\n{YELLOW}TEST 5: Checking Local Server{RESET}")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("http://127.0.0.1:8000/health")
            if r.status_code == 200:
                data = r.json()
                ok(f"Server is running! Status: {data.get('status')}")
                ok(f"Active conversations: {data.get('active_conversations')}")
            else:
                fail(f"Server returned status {r.status_code}")
    except:
        fail("Server is NOT running on port 8000!")
        warn("Start it with: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    header("DIAGNOSTIC SUMMARY")
    print(f"  If all tests passed above, your bot should be working.")
    print(f"  If you're still not getting replies on WhatsApp, check:")
    print(f"")
    print(f"  1. {YELLOW}Is ngrok running?{RESET}")
    print(f"     Run: ngrok http 8000")
    print(f"     Copy the https:// URL")
    print(f"")
    print(f"  2. {YELLOW}Is the webhook URL updated in Meta Dashboard?{RESET}")
    print(f"     Go to: developers.facebook.com/apps > WhatsApp > Configuration")
    print(f"     Webhook URL must be: https://YOUR-NGROK-URL/webhook")
    print(f"     (ngrok URLs change every time you restart ngrok!)")
    print(f"")
    print(f"  3. {YELLOW}Did you subscribe to 'messages'?{RESET}")
    print(f"     In the same webhook config, make sure 'messages' is subscribed")
    print(f"")
    print(f"  4. {YELLOW}24-hour messaging window{RESET}")
    print(f"     You can only reply within 24h of the user's last message")
    print(f"     The user must message your business number FIRST")
    print()


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
