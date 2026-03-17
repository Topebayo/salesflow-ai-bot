import httpx
import os
import sys
import json
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

token = os.getenv('WHATSAPP_ACCESS_TOKEN')
phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

# Check available templates
url = f'https://graph.facebook.com/v18.0/{phone_id}/message_templates'
r = httpx.get(url, headers={'Authorization': f'Bearer {token}'})
print('Templates Status:', r.status_code)

if r.status_code == 200:
    data = r.json()
    templates = data.get('data', [])
    print(f'Templates found: {len(templates)}')
    for t in templates:
        print(f"  - {t.get('name')} ({t.get('status')}) lang:{t.get('language')}")
else:
    print('Error:', r.text)

# Try sending with order_details template
print('\n--- Sending test message ---')
msg_url = f'https://graph.facebook.com/v18.0/{phone_id}/messages'
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Try a simple text message first (works if there's an open conversation window)
payload = {
    'messaging_product': 'whatsapp',
    'to': '2349155118839',
    'type': 'text',
    'text': {
        'preview_url': False,
        'body': 'Hello! This is a test from your AI Sales Agent bot.'
    }
}

r = httpx.post(msg_url, headers=headers, json=payload)
print('Text message status:', r.status_code)
print('Response:', r.text)
