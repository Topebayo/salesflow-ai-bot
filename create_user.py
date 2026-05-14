import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# We use the Service Role key to bypass rate limits!
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")  # This is the secret service_role key
supabase: Client = create_client(url, key)

email = "demo@salesflow.ai"
password = "password123"
business_name = "Tope's Demo Properties"

try:
    print(f"Creating user {email}...")
    # 1. Create the user in Auth (bypassing rate limits using admin api)
    user = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"business_name": business_name}
    })
    
    print(f"User created successfully! ID: {user.user.id}")
    
    # 2. Create the business profile
    supabase.table("businesses").insert({
        "owner_id": user.user.id,
        "name": business_name,
        "bot_mode": "real_estate"
    }).execute()
    
    print("Business profile created! You can now log in.")
    print(f"Email: {email}")
    print(f"Password: {password}")
except Exception as e:
    print(f"Error: {e}")
