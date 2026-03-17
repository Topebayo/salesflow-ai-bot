import httpx
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

r = httpx.get('http://127.0.0.1:4040/api/requests/http')
data = r.json()
requests_list = data.get('requests', [])

print(f"Total ngrok requests captured: {len(requests_list)}")
print("=" * 60)

for i, req in enumerate(requests_list):
    print(f"\nRequest #{i+1}:")
    
    # Try different key names
    method = req.get('method', req.get('request', {}).get('method', 'N/A'))
    uri = req.get('uri', req.get('request', {}).get('uri', 'N/A'))
    status = req.get('status', req.get('response', {}).get('status', 'N/A'))
    
    # Get request details
    request_info = req.get('request', {})
    response_info = req.get('response', {})
    
    print(f"  Method: {request_info.get('method', 'N/A')}")
    print(f"  URI: {request_info.get('uri', 'N/A')}")
    print(f"  Response Status: {response_info.get('status', 'N/A')}")
    
    # Try to get request body
    raw = request_info.get('raw', '')
    if raw:
        print(f"  Has request body: Yes")
    
    print("-" * 40)
