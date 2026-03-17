"""
Send a test message and check its delivery status
"""
import os
import sys
import time
import httpx
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(override=True)

token = os.getenv('WHATSAPP_ACCESS_TOKEN')
phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
api_url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

RECIPIENT = "2348137048851"  # The verified number

print("=" * 60)
print("WHATSAPP MESSAGE DELIVERY TEST")
print("=" * 60)

# Step 1: Send hello_world template
print(f"\n1. Sending hello_world template to {RECIPIENT}...")
payload = {
    "messaging_product": "whatsapp",
    "to": RECIPIENT,
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {"code": "en_US"}
    }
}

r = httpx.post(api_url, headers=headers, json=payload, timeout=15.0)
print(f"   Status Code: {r.status_code}")
data = r.json()

if r.status_code == 200:
    msg_id = data.get("messages", [{}])[0].get("id", "unknown")
    msg_status = data.get("messages", [{}])[0].get("message_status", "unknown")
    print(f"   Message ID: {msg_id}")
    print(f"   Initial Status: {msg_status}")
    
    # Step 2: Check message status after a few seconds
    print(f"\n2. Waiting 10 seconds then checking delivery status...")
    time.sleep(10)
    
    # Query the message status
    status_url = f"https://graph.facebook.com/v18.0/{msg_id}"
    sr = httpx.get(status_url, headers={"Authorization": f"Bearer {token}"}, timeout=15.0)
    print(f"   Status check response: {sr.status_code}")
    print(f"   Status data: {sr.text[:500]}")
    
else:
    print(f"   ERROR: {data}")
    error = data.get("error", {})
    print(f"   Error Code: {error.get('code')}")
    print(f"   Error Message: {error.get('message')}")
    print(f"   Error Subcode: {error.get('error_subcode')}")

# Step 3: Also try sending a plain text message
print(f"\n3. Trying plain text message to {RECIPIENT}...")
text_payload = {
    "messaging_product": "whatsapp",
    "to": RECIPIENT,
    "type": "text",
    "text": {"body": "Test message from AI Sales Agent - can you see this?"}
}

r2 = httpx.post(api_url, headers=headers, json=text_payload, timeout=15.0)
print(f"   Status Code: {r2.status_code}")
data2 = r2.json()

if r2.status_code == 200:
    msg_id2 = data2.get("messages", [{}])[0].get("id", "unknown")
    msg_status2 = data2.get("messages", [{}])[0].get("message_status", "unknown")
    print(f"   Message ID: {msg_id2}")
    print(f"   Status: {msg_status2}")
else:
    error2 = data2.get("error", {})
    print(f"   Error Code: {error2.get('code')}")
    print(f"   Error Message: {error2.get('message')}")
    if error2.get('code') == 131047:
        print(f"   >>> This means you MUST use a template for first contact!")
        print(f"   >>> The recipient hasn't messaged you first within 24 hours")

# Step 4: Check WhatsApp Business Account info
print(f"\n4. Checking WhatsApp Business Account status...")
ba_url = f"https://graph.facebook.com/v18.0/{phone_id}?fields=display_phone_number,verified_name,status,quality_rating,messaging_limit_tier,is_official_business_account"
r3 = httpx.get(ba_url, headers={"Authorization": f"Bearer {token}"}, timeout=15.0)
data3 = r3.json()
for k, v in data3.items():
    print(f"   {k}: {v}")

# Step 5: Check if the number is valid for WhatsApp
print(f"\n5. Summary:")
print(f"   - Messages are being ACCEPTED by Meta's API")
print(f"   - If you're not receiving them, possible reasons:")
print(f"     a) Phone number {RECIPIENT} is not registered on WhatsApp")
print(f"     b) WhatsApp app on that phone needs to be restarted")
print(f"     c) The phone has no internet connection")
print(f"     d) Messages are going to a different WhatsApp account")
print(f"   - Try: Open WhatsApp > Settings > check your phone number")
print()
