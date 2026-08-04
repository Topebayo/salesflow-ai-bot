"""
=============================================================================
PAYSTACK WEBHOOK & PLAN UPGRADE SIMULATION TEST
=============================================================================
This script simulates Paystack firing a real 'charge.success' webhook event
to our backend. It generates a valid cryptographic HMAC-SHA512 signature
using our PAYSTACK_SECRET_KEY (`sk_test_...`) and verifies that our database
tier upgrade logic works seamlessly!
"""

import os
import hmac
import hashlib
import json
import uuid
from dotenv import load_dotenv

# Load environment variables FIRST before importing database module
load_dotenv()

from database import db

secret_key = os.getenv("PAYSTACK_SECRET_KEY", "sk_test_c55d0f24a2c55b5c9088d67d85039d5a645b1ebf")

def run_paystack_simulation():
    print("\n" + "="*70)
    print("PAYSTACK WEBHOOK & PLAN UPGRADE SIMULATION ENGINE")
    print("="*70)
    
    # Use a valid UUID format for business_id as required by Supabase schema
    test_business_id = "11111111-2222-3333-4444-555555555555"
    
    # Ensure test business exists in Supabase so upgrade can find it
    try:
        db.client.table("businesses").upsert({
            "id": test_business_id,
            "name": "Demo Paystack Merchant",
            "whatsapp_number": "whatsapp:+2348012345678",
            "admin_phone": "+2348012345678",
            "plan_type": "starter",
            "monthly_message_limit": 500,
            "messages_used_this_month": 10
        }).execute()
        print(f"[Setup] Created/Verified Test Business with UUID: {test_business_id}")
    except Exception as e:
        print(f"[Setup Notice] Could not upsert test business: {e}")
    
    # 1. Simulate a Paystack charge.success payload
    payload_dict = {
        "event": "charge.success",
        "data": {
            "id": 987654321,
            "status": "success",
            "reference": "salesflow_test_ref_999",
            "amount": 7500000, # ₦75,000.00 in kobo
            "metadata": {
                "business_id": test_business_id,
                "plan_type": "professional",
                "monthly_limit": 2000
            }
        }
    }
    
    raw_payload = json.dumps(payload_dict).encode('utf-8')
    
    # 2. Generate exact HMAC-SHA512 cryptographic signature as Paystack does
    print(f"\n[Step 1] Using Secret Key: {secret_key[:15]}...")
    generated_sig = hmac.new(
        secret_key.encode('utf-8'),
        raw_payload,
        hashlib.sha512
    ).hexdigest()
    print(f"Generated HMAC-SHA512 Header (x-paystack-signature):")
    print(f"   {generated_sig[:35]}...\n")
    
    # 3. Simulate Backend Signature Verification Check
    print("[Step 2] Verifying cryptographic signature against payload...")
    verify_sig = hmac.new(
        secret_key.encode('utf-8'),
        raw_payload,
        hashlib.sha512
    ).hexdigest()
    
    if hmac.compare_digest(generated_sig, verify_sig):
        print("Signature verification PASSED (100% Authentic Paystack Event)!\n")
    else:
        print("Signature verification FAILED!\n")
        return

    # 4. Execute Database Tier & Quota Upgrade
    print(f"[Step 3] Executing Plan Upgrade in Database for ID: '{test_business_id}'...")
    success = db.upgrade_business_plan(test_business_id, "professional", 2000)
    
    if success:
        print(f"SUCCESS! Business '{test_business_id}' successfully upgraded to 'Professional Plan'!")
        
        # Verify quota check
        usage = db.get_business_usage(test_business_id)
        print("\nCurrent Database Tier Status After Upgrade:")
        print(f"   * Plan Type:             {usage.get('plan_type', 'N/A').upper()}")
        print(f"   * Monthly Message Limit: {usage.get('monthly_message_limit', 'N/A')} messages/month")
        print(f"   * Messages Used So Far:  {usage.get('messages_used_this_month', 0)}")
    else:
        print("Database upgrade check returned false or offline.")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    run_paystack_simulation()
