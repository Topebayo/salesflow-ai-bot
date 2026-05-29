import sys
import asyncio
from dotenv import load_dotenv

# Set stdout to UTF-8 to prevent encoding errors on Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from database import db
from ai_engine import ai_engine

async def chat_loop():
    print("=" * 60)
    print("🤖 WHATSAPP AI AGENT - LOCAL TERMINAL TESTING SUITE 🤖")
    print("=" * 60)
    
    # 1. Fetch businesses
    try:
        res = db.client.table("businesses").select("id, name, bot_mode").execute()
        businesses = res.data
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return

    if not businesses:
        print("❌ No businesses found in the database. Please create one first.")
        return

    print("\nAvailable Businesses (Tenants):")
    for idx, b in enumerate(businesses):
        print(f"  [{idx + 1}] {b['name']} ({b['bot_mode']})")
    
    try:
        selection = input("\nSelect a business to chat with (number): ").strip()
        biz_idx = int(selection) - 1
        if biz_idx < 0 or biz_idx >= len(businesses):
            raise ValueError()
    except (ValueError, IndexError):
        print("❌ Invalid selection. Exiting.")
        return

    selected_biz = businesses[biz_idx]
    business_id = selected_biz["id"]
    business_name = selected_biz["name"]
    
    print(f"\n🔌 Connected to test agent for: '{business_name}'")
    print("Commands:")
    print("  type 'clear' to clear conversation memory.")
    print("  type 'exit' to quit.")
    print("-" * 60)

    phone_number = "+2348011112222"
    
    # Check if a custom greeting exists
    config = db.get_business_config(business_id)
    greeting = config.get("greeting")
    if greeting:
        print(f"\n🤖 {config.get('agent_name', 'AI')}: {greeting}")
    else:
        print(f"\n🤖 {config.get('agent_name', 'AI')}: Hello! How can I help you today?")

    while True:
        try:
            user_msg = input("\n👤 Customer: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
            
        if not user_msg:
            continue
            
        if user_msg.lower() == 'exit':
            print("Goodbye!")
            break
            
        if user_msg.lower() == 'clear':
            db.clear_conversation(business_id, phone_number)
            print("🗑️ Conversation memory cleared!")
            continue

        # Generate response using Groq/Gemini via AI engine
        print("🤖 AI is thinking...")
        ai_reply = await ai_engine.generate_response(
            business_id=business_id,
            phone_number=phone_number,
            user_message=user_msg
        )
        
        # Check for image tokens and mock-resolve them
        import re
        image_tokens = re.findall(r'\[IMAGE:([a-zA-Z0-9\-]+)\]', ai_reply)
        clean_reply = re.sub(r'\[IMAGE:[a-zA-Z0-9\-]+\]', '', ai_reply).strip()
        
        print(f"\n🤖 Agent: {clean_reply}")
        
        if image_tokens:
            print("\n🖼️ [MOCK WHATSAPP MEDIA TRIGGERED]")
            for prod_id in image_tokens:
                product = db.get_product_by_id(prod_id)
                if product:
                    print(f"  * Sent Image: {product['image_url']}")
                    print(f"  * Caption: {product['name']} — ₦{product.get('price', '0')}")
                else:
                    print(f"  * Sent Image: [Invalid Product ID: {prod_id}]")

if __name__ == "__main__":
    asyncio.run(chat_loop())
