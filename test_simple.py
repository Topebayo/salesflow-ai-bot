"""
Simple diagnostic test - writes results to a file
"""
import asyncio
import sys
import os
import httpx
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

results = []

def log(text):
    results.append(text)
    print(text)


async def run():
    log("=" * 60)
    log("WHATSAPP AI SALES AGENT - DIAGNOSTIC TEST")
    log("=" * 60)
    
    # TEST 1: Environment Variables
    log("\nTEST 1: Environment Variables")
    log("-" * 40)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    wa_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    wa_verify = os.getenv("WHATSAPP_VERIFY_TOKEN")
    wa_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if gemini_key:
        log(f"  OK - GEMINI_API_KEY: {gemini_key[:10]}...{gemini_key[-5:]}")
    else:
        log("  FAIL - GEMINI_API_KEY: NOT SET")
        return
    
    if wa_token:
        log(f"  OK - WHATSAPP_ACCESS_TOKEN: {wa_token[:15]}...{wa_token[-10:]}")
    else:
        log("  FAIL - WHATSAPP_ACCESS_TOKEN: NOT SET")
        return
    
    if wa_verify:
        log(f"  OK - WHATSAPP_VERIFY_TOKEN: {wa_verify}")
    else:
        log("  FAIL - WHATSAPP_VERIFY_TOKEN: NOT SET")
    
    if wa_phone_id:
        log(f"  OK - WHATSAPP_PHONE_NUMBER_ID: {wa_phone_id}")
    else:
        log("  FAIL - WHATSAPP_PHONE_NUMBER_ID: NOT SET")
        return
    
    # TEST 2: AI Engine
    log("\nTEST 2: AI Engine (Gemini)")
    log("-" * 40)
    
    try:
        from ai_engine import ai_engine
        log("  OK - AI Engine imported")
        
        response = await ai_engine.generate_response(
            phone_number="+2340000000000",
            user_message="Hello, I need help"
        )
        
        if response:
            log(f"  OK - AI Response generated ({len(response)} chars)")
            log(f"  Preview: {response[:150]}...")
        else:
            log("  FAIL - AI returned empty response!")
        
        ai_engine.clear_conversation("+2340000000000")
    except Exception as e:
        log(f"  FAIL - AI Engine error: {str(e)}")
        return
    
    # TEST 3: WhatsApp API Token
    log("\nTEST 3: WhatsApp API Token Validation")
    log("-" * 40)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            check_url = f"https://graph.facebook.com/v18.0/{wa_phone_id}"
            r = await client.get(
                check_url,
                headers={"Authorization": f"Bearer {wa_token}"}
            )
            
            if r.status_code == 200:
                data = r.json()
                log(f"  OK - Token is VALID")
                log(f"  OK - Phone: {data.get('display_phone_number', 'N/A')}")
                log(f"  OK - Name: {data.get('verified_name', 'N/A')}")
            else:
                error_data = r.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown")
                error_code = error_data.get("error", {}).get("code", "N/A")
                log(f"  FAIL - Status: {r.status_code}")
                log(f"  FAIL - Error Code: {error_code}")
                log(f"  FAIL - Error: {error_msg}")
                
                if error_code == 190 or "expired" in str(error_msg).lower():
                    log("")
                    log("  >>> YOUR ACCESS TOKEN HAS EXPIRED! <<<")
                    log("  >>> Go to: https://developers.facebook.com/apps/")
                    log("  >>> Navigate to: Your App > WhatsApp > API Setup")
                    log("  >>> Generate a new token and update your .env file")
                return
                
    except Exception as e:
        log(f"  FAIL - Connection error: {str(e)}")
        return
    
    # TEST 4: Server check
    log("\nTEST 4: Local Server Check")
    log("-" * 40)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("http://127.0.0.1:8000/health")
            if r.status_code == 200:
                log(f"  OK - Server running on port 8000")
            else:
                log(f"  FAIL - Server returned {r.status_code}")
    except:
        log("  WARN - Server NOT running on port 8000")
        log("  Start with: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
    # SUMMARY
    log("\n" + "=" * 60)
    log("NEXT STEPS IF TESTS PASSED:")
    log("=" * 60)
    log("1. Start server: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    log("2. Start ngrok:  ngrok http 8000")
    log("3. Copy the https:// URL from ngrok")
    log("4. Go to Meta Developer Console > WhatsApp > Configuration")
    log("5. Update webhook URL to: https://YOUR-NGROK-URL/webhook")
    log("6. Verify Token must match: " + str(wa_verify))
    log("7. Subscribe to 'messages' field")
    log("8. Send a message from WhatsApp to your business number")
    
    # Write results to file
    with open("diagnostic_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    log("\nResults saved to diagnostic_results.txt")


if __name__ == "__main__":
    asyncio.run(run())
