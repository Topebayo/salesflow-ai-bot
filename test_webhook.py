import sys
import httpx
from dotenv import load_dotenv

# Set stdout to UTF-8 to prevent encoding errors on Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from database import db

def run_webhook_test():
    print("=" * 60)
    print("📨 WHATSAPP AI AGENT - MOCK WEBHOOK INBOUND TESTER 📨")
    print("=" * 60)
    
    # 1. Fetch businesses
    try:
        res = db.client.table("businesses").select("id, name, bot_mode").execute()
        businesses = res.data
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return

    if not businesses:
        print("❌ No businesses found in the database.")
        return

    print("\nSelect a business to trigger a webhook for:")
    for idx, b in enumerate(businesses):
        print(f"  [{idx + 1}] {b['name']} ({b['bot_mode']})")
    
    try:
        selection = input("\nSelect (number): ").strip()
        biz_idx = int(selection) - 1
        if biz_idx < 0 or biz_idx >= len(businesses):
            raise ValueError()
    except (ValueError, IndexError):
        print("❌ Invalid selection. Exiting.")
        return

    selected_biz = businesses[biz_idx]
    business_id = selected_biz["id"]
    
    message_body = input("\nEnter mock message to send to the bot (e.g. 'do you have any duplexes?'): ").strip()
    if not message_body:
        print("❌ Empty message. Exiting.")
        return

    url = f"http://localhost:8000/webhook/{business_id}"
    
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid.mock_webhook_test_msg_id",
                                    "from": "2348098765432",
                                    "type": "text",
                                    "text": {
                                        "body": message_body
                                                    }
                                                }
                                            ],
                                            "contacts": [
                                                {
                                                    "profile": {
                                                        "name": "Local Tester"
                                                    },
                                                    "wa_id": "2348098765432"
                                                }
                                            ]
                                        },
                                        "field": "messages"
                                    }
                                ]
                            }
                        ]
                    }

    print(f"\n📡 Sending POST request to local server: {url}")
    print(f"💬 Payload Message: \"{message_body}\"")
    
    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        print(f"\n✅ Webhook Response Status: {response.status_code}")
        print(f"✅ Webhook Response Body: {response.text}")
        print("\n👉 Check the console logs of your running FastAPI server to see the background AI execution and database logs!")
    except Exception as e:
        print(f"❌ Error sending request: {e}")
        print("👉 Make sure your FastAPI server is currently running (python main.py) on port 8000!")

if __name__ == "__main__":
    run_webhook_test()
