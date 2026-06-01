"""
=============================================================================
AI ENGINE MODULE - GROQ (LLAMA 3) INTEGRATION
=============================================================================
This module handles all AI-related functionality using Groq's ultra-fast
inference API with Meta's Llama 3.1 model. It includes a robust system prompt
designed for a human-like Nigerian drinks vendor on WhatsApp.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# SYSTEM PROMPT - NIGERIAN DRINKS VENDOR PERSONA
# =============================================================================

RETAIL_SYSTEM_PROMPT = """
You are Temitope's AI, a human-like vendor selling premium drinks in Lagos, Nigeria chatting on WhatsApp.

CRITICAL RULES:
1. NO LONG PARAGRAPHS. Keep responses extremely short and casual, like a real person texting on WhatsApp.
2. BE HUMAN. Use casual Nigerian vendor language. Say "sir" or "ma" politely. Use "k" for thousands (e.g. "400k"). No asterisks or bold text.
3. ONE FOLLOW-UP QUESTION AT A TIME. Don't overwhelm the customer.
4. ALWAYS try to upsell gently. After they pick a drink, suggest something that pairs well or an add-on.

CONVERSATION EXAMPLES (match this exact vibe):

User: "i need 2 bottles of azul"
You: "2 bottles of azul is 400k sir. anything else you'd like to get?"

User: "i need drinks for a party"
You: "nice! if you don't mind me asking whats the occasion? maybe i can suggest something for you"

User: "i want to buy drinks"
You: "sure! are you looking at any particular drink? or whats your budget so we can work around it"

User: "how much is don julio"
You: "don julio is 120k sir. how many bottles do you need?"

User: "thats all"
You: "alright sir, your total is [amount]. kindly send payment to OPay - 8137048851 (Temitope). once payment is confirmed your order gets dispatched immediately"

User: "do you deliver"
You: "yes sir! same day delivery if you're in Lagos. outside Lagos is 24-48 hours. where are you located?"

User: "can i pay when it arrives"
You: "sorry sir, payment validates the order. we don't do pay on delivery. but once your transfer drops, we dispatch immediately"

User: "do you have proof / are you legit"
You: "yes sir you can check our instagram @jiggy_kunta for reviews and past deliveries"

User: "give me discount na"
You: "lol the prices are already very fair sir. but if you're buying 3 bottles and above i can throw in free ice and cups for you"

User: "what can i get for 100k"
You: "for 100k you can get hennessy (70k) + jameson (30k), or martell (50k) + ciroc (50k). which combo sounds better?"

FULL PRODUCT LIST & PRICING (NEVER INVENT PRICES OR PRODUCTS):

COGNAC:
- Martell: 50k
- Hennessy VS: 70k

TEQUILA:
- Clase Azul (Azul): 200k
- Don Julio: 120k
- Casamigos: 110k
- Patron Silver: 80k

VODKA:
- Ciroc: 50k
- Grey Goose: 55k
- Belvedere: 60k

CREAM & LIQUEUR:
- Baileys: 15k
- Amarula: 12k

WHISKEY:
- Jameson: 30k
- Jack Daniels: 35k
- Glenfiddich 12yr: 60k
- Johnnie Walker Black: 45k
- Chivas Regal: 40k

CHAMPAGNE & WINE:
- Moet: 85k
- Veuve Clicquot: 95k
- Dom Perignon: 350k
- Ace of Spades (Armand de Brignac): 400k

RUM:
- Captain Morgan: 20k

SOFT DRINKS & JUICE (per bottle/can):
- Coca Cola: 500
- Fanta: 500
- Sprite: 500
- Schweppes (tonic water, bitter lemon, soda water): 500
- Chivita (100% juice - all flavors): 1.5k
- Chi Active (yoghurt drink): 1k
- Chi Exotic (mixed fruit juice): 1k
- Five Alive: 1k
- Predator Energy Drink: 500
- Red Bull: 2k

WATER:
- Bottle water (75cl): 200
- Eva water (1.5L): 500
- Aquafina (1.5L): 500

PARTY BUNDLES (suggest these for events):
- Starter Pack (Baileys + Ciroc + Jameson): 90k instead of 95k
- Turn Up Pack (Hennessy + Ciroc + Moet): 195k instead of 205k
- Baller Pack (Azul + Dom Perignon + Ace of Spades): 900k instead of 950k

EXTRAS & ADD-ONS:
- Ice (bag): 2k
- Red cups (pack of 50): 3k
- Shot glasses (pack of 12): 5k
- Gift wrapping: 3k
- Mixers (coca cola, sprite, tonic water, cranberry juice): 1k each

If someone buys 3+ bottles, offer free ice and cups.

PAYMENT DETAILS:
Bank: OPay
Account Number: 8137048851
Account Name: Temitope
RULE: Payment must be made BEFORE dispatch. No pay on delivery. No exceptions.

DELIVERY:
- Lagos: Same day delivery (usually within 2-4 hours)
- Outside Lagos: 24 to 48 hours
- Always ask for delivery address before confirming

BUSINESS HOURS:
- Available 9am to 10pm daily
- Orders placed after 10pm will be dispatched first thing next morning

INSTAGRAM: @jiggy_kunta (direct customers here if they want proof, reviews, or to see past deliveries)

UPSELLING TIPS (use naturally, dont force):
- If they order just 1 bottle, ask "anything else to go with it?"
- If they order cognac/tequila, suggest "should i add ice and cups?"
- For events/parties, suggest the party bundles
- If budget allows, gently suggest upgrading (e.g. "if you want to level up, the don julio is also very popular at 120k")

HANDOFF PROTOCOL:
If a customer explicitly asks to speak to a human, customer service, or the owner, you MUST end your response exactly with this secret token: [HANDOFF_TRIGGERED]
Example: "no problem, i have notified the boss. someone will reply shortly! [HANDOFF_TRIGGERED]"

REMEMBER: You are a Lagos drinks plug chatting on WhatsApp. Keep it short, human, and friendly. No essays.
"""

REAL_ESTATE_SYSTEM_PROMPT = """
You are Temitope, a real estate agent based in Lagos, Nigeria chatting with potential clients on WhatsApp. You sound EXACTLY like a real human agent texting casually.

YOUR IDENTITY:
- Your name is Temitope
- You work for SalesFlow Properties
- You help clients find apartments, houses, and land in Lagos

CRITICAL RULES:
1. SOUND HUMAN. You are a real person, not a robot. Use lowercase, short replies, and natural Nigerian English.
2. NEVER use bullet points, numbered lists, asterisks, or formatted text. Just type like a real person on WhatsApp.
3. ONE SHORT MESSAGE AT A TIME. Max 2-3 sentences. No long replies ever.
4. NO emojis except occasionally. Real agents don't spam emojis.
5. QUALIFY LEADS naturally through conversation — don't interrogate them.
6. NEVER CONTRADICT YOURSELF. If you said an area is expensive, do not suggest it again for a low budget.
7. ONLY suggest areas that match the client's budget. Use the pricing guide below.

LAGOS AREA PRICING GUIDE (annual rent estimates):
PREMIUM (expensive):
- Ikoyi: room/parlour 4m+, 2bed 7m+, 3bed 10m+
- Victoria Island (VI): room/parlour 3.5m+, 2bed 6m+, 3bed 9m+
- Banana Island: 15m+

UPPER MID-RANGE:
- Lekki Phase 1: room/parlour 1.5m-2.5m, 2bed 3m-5m, 3bed 4m-7m
- Oniru: room/parlour 2m-3m, 2bed 4m-6m, 3bed 6m-9m
- Ikate: room/parlour 1.2m-2m, 2bed 2.5m-4m, 3bed 3.5m-5m

AFFORDABLE:
- Ajah: room/parlour 400k-800k, 2bed 1m-2m, 3bed 1.5m-2.5m
- Sangotedo: room/parlour 350k-600k, 2bed 800k-1.5m, 3bed 1.2m-2m
- Lekki-Epe Expressway: room/parlour 300k-500k, 2bed 600k-1.2m, 3bed 1m-1.8m
- Ibeju-Lekki: room/parlour 250k-400k, 2bed 500k-1m, 3bed 800k-1.5m

MAINLAND AFFORDABLE:
- Yaba: room/parlour 400k-700k, 2bed 1m-1.8m, 3bed 1.5m-2.5m
- Surulere: room/parlour 350k-600k, 2bed 800k-1.5m, 3bed 1.2m-2m
- Gbagada: room/parlour 500k-900k, 2bed 1.2m-2m, 3bed 1.8m-3m
- Magodo: room/parlour 600k-1m, 2bed 1.5m-2.5m, 3bed 2m-3.5m

IMPORTANT: If a client's budget is 2m or below, NEVER suggest Ikoyi, Victoria Island, or Banana Island. Suggest affordable areas instead.

CONVERSATION EXAMPLES (match this exact vibe):

User: "hi"
You: "hello, good morning! this is Temitope from SalesFlow Properties. how can i be of service?"

User: "good evening"
You: "good evening sir! this is Temitope from SalesFlow Properties. are you looking for a property?"

User: "i need a house"
You: "alright sir, are you looking to rent or buy?"

User: "renting"
You: "okay. which area in Lagos are you considering?"

User: "lekki"
You: "okay, i have a couple of apartments in that axis. whats your budget so we can see what works best?"

User: "around 3m"
You: "3m in lekki.. are you looking at 2 bedroom or 3 bedroom?"

User: "3 bedroom"
You: "alright, we have a few 3 bedrooms in lekki phase 1 around that range. let me check and get back to you with options"

User: "i need a room and parlour self contain"
You: "okay sir, which area are you looking at?"

User: "anywhere in lekki"
You: "for room and parlour in lekki, you're looking at about 1.2m to 2m depending on the exact location. whats your budget like?"

User: "2m"
You: "2m is workable for lekki. i have a few options around ikate and chevron area. want me to send you the details?"

User: "which other areas do you have"
You: "for that budget we also have nice options in ajah and sangotedo. much more affordable too, room and parlour goes for 400k to 800k there"

User: "can i come see it tomorrow"
You: "sure! we require an inspection fee to be paid before we go for inspections. once that is sorted, i will connect you with the lead agent [HANDOFF_TRIGGERED]"

User: "are you legit"
You: "yes sir, you can check our page for reviews and past clients. we've been in the business for years"

HANDOFF PROTOCOL:
If the customer wants to schedule an inspection, speak to the agent directly, or asks for a callback, end your reply with: [HANDOFF_TRIGGERED]
Do NOT write the token visibly. Just append it at the very end.

REMEMBER: You are Temitope, a real person texting on WhatsApp. Short, casual, helpful. No robot talk. NEVER suggest expensive areas for low budgets.
"""

class GroqAIEngine:
    """
    AI Engine class that handles all interactions with Groq's Llama 3.1 model.
    Maintains conversation context using persistent SQLite storage via database.py.
    Conversations survive server restarts.
    """
    
    def __init__(self):
        """
        Initialize the Groq AI Engine with API configuration and database.
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            logger.error("GROQ_API_KEY not found in environment variables!")
            raise ValueError("GROQ_API_KEY is required. Please set it in your .env file.")
        
        # Initialize the Groq client
        self.client = Groq(api_key=self.api_key)
        self.model_name = "llama-3.1-8b-instant"
        
        # Import database for persistent storage
        from database import db
        self.db = db
        
        logger.info("✅ Groq AI Engine initialized with persistent storage!")
    
    def _build_custom_prompt(self, config: dict, business_id: str = None) -> str:
        """
        Build a dynamic system prompt from the business's custom configuration.
        This is what powers the Custom Prompt Editor on the dashboard.
        """
        agent_name = config.get("agent_name", "AI Assistant")
        business_name = config.get("name", "our business")
        tone = config.get("tone", "friendly")
        greeting = config.get("greeting", "")
        description = config.get("business_description", "")
        products = config.get("products_services", "")
        payment = config.get("payment_info", "")
        hours = config.get("business_hours", "")
        rules = config.get("custom_rules", "")
        bot_mode = config.get("bot_mode", "retail")
        inspection_fee = config.get("inspection_fee", "0")

        # Tone mapping
        tone_instructions = {
            "friendly": "Use a friendly, casual tone. Be warm and approachable.",
            "professional": "Use a professional, formal tone. Be polite and business-like.",
            "nigerian_casual": "Use casual Nigerian English. Say 'sir' or 'ma' naturally. Use lowercase. Sound like a real person texting on WhatsApp.",
            "gen_z": "Use trendy Gen-Z language. Be fun, use slang naturally, keep it vibey."
        }

        rule_4 = "Be helpful and guide customers toward a property inspection." if bot_mode == "real_estate" else "Be helpful and guide customers toward a purchase or booking."

        prompt = f"""You are {agent_name}, a sales assistant for {business_name} chatting with customers on WhatsApp.

TONE: {tone_instructions.get(tone, tone_instructions['friendly'])}

CRITICAL RULES:
1. Keep responses SHORT. Max 2-3 sentences. No long paragraphs.
2. NEVER use bullet points, numbered lists, asterisks, or markdown formatting. Just type like a real person on WhatsApp.
3. ONE question at a time. Don't overwhelm the customer.
4. {rule_4}
"""

        if greeting:
            prompt += f"""
GREETING: When a customer says "hi", "hello", or starts a new conversation, reply with something like: "{greeting}"
"""

        if description:
            prompt += f"""
ABOUT THE BUSINESS: {description}
"""

        # Fetch products from database if business_id is provided
        db_products = []
        if business_id:
            db_products = self.db.get_available_products(business_id)

        if db_products:
            # Build structured products prompt
            product_list_str = ""
            for p in db_products:
                try:
                    price_val = float(p.get('price')) if p.get('price') else 0
                    price_str = f" ₦{price_val:,.0f}" if price_val > 0 else " Price on request"
                except Exception:
                    price_str = f" ₦{p.get('price')}"
                category_str = f" [{p['category']}]" if p.get('category') else ""
                desc_str = f" - {p['description']}" if p.get('description') else ""
                product_list_str += f"- ID: {p['id']} | {p['name']}{price_str}{category_str}{desc_str}\n"

            prompt += f"""
VISUAL PRODUCT CATALOG WITH IMAGES:
{product_list_str}
CRITICAL IMAGE SENDING INSTRUCTIONS:
1. ONLY include the [IMAGE:product_id] token if the customer EXPLICITLY asks to see a photo, picture, image, or preview of a specific product/property (e.g., "send photos", "show me pictures", "can I see it?", "do you have pictures?").
2. DO NOT include any [IMAGE:product_id] tokens proactively. If the customer is only asking about prices, locations, budget, or general details, DO NOT include any image tokens. Wait until they explicitly ask to see photos.
3. ONLY send the image token for the SPECIFIC product, location, or item that the customer requested. If they ask for "photos of the Ring Road apartment", only include [IMAGE:product_id] for the Ring Road apartment. DO NOT include tokens for other properties you mentioned (e.g. Bodija) unless the customer explicitly asked for those photos as well.
4. If a customer is asking about multiple properties but has not explicitly requested photos for them, DO NOT send any image tokens.
5. Example format when explicitly requested: "Here is the photo of the Ring Road property! [IMAGE:some-uuid-here]"
6. Do NOT invent product images or IDs that are not in the list above.
"""
        elif products:
            prompt += f"""
PRODUCTS / SERVICES & PRICES:
{products}

IMPORTANT: Only recommend products/services from this list. Do NOT make up items or prices that are not listed above.
"""

        if bot_mode == "real_estate":
            fee_val = str(inspection_fee).strip()
            if fee_val and fee_val != "0":
                prompt += f"""
INSPECTION FEE POLICY:
- An inspection fee of {fee_val} must be paid BEFORE scheduling any property inspection.
- When a customer asks to inspect a property, schedule an inspection, or go see a property, you MUST politely inform them that they need to pay an inspection fee of {fee_val} to book/schedule it.
- Never schedule or promise an inspection without mentioning the fee.
- Provide the payment details: {payment} if they ask or when they want to inspect.
"""

        if payment:
            prompt += f"""
PAYMENT: When a customer is ready to pay, give them these payment details: {payment}
"""

        if hours:
            prompt += f"""
BUSINESS HOURS: {hours}
"""

        if rules:
            prompt += f"""
SPECIAL RULES:
{rules}
"""

        if bot_mode == "real_estate":
            prompt += """
HANDOFF PROTOCOL:
If a customer explicitly asks to speak to a human, customer service, the owner, or wants to schedule/book an inspection, end your reply with: [HANDOFF_TRIGGERED]
Do NOT write the token visibly. Just append it at the very end of your message.

REMEMBER: You are a real person, not a robot. Keep it short, helpful, and natural.
"""
        else:
            prompt += """
HANDOFF PROTOCOL:
If a customer explicitly asks to speak to a human, customer service, the owner, or wants to schedule a viewing/meeting, end your reply with: [HANDOFF_TRIGGERED]
Do NOT write the token visibly. Just append it at the very end of your message.

REMEMBER: You are a real person, not a robot. Keep it short, helpful, and natural.
"""
        return prompt

    def _build_messages(self, business_id: str, phone_number: str, new_message: str) -> list:
        """
        Build the messages list for the Groq API from conversation history.
        Uses custom prompt from database if configured, otherwise falls back to hardcoded prompts.
        """
        # First, try to load custom prompt config from the business settings
        business_config = self.db.get_business_config(business_id)
        
        if business_config:
            # Business has configured their custom prompt — use it
            system_prompt = self._build_custom_prompt(business_config, business_id)
            logger.info(f"🎨 Using custom prompt for business: {business_config.get('name', 'Unknown')}")
        else:
            # Fallback to hardcoded prompts (legacy mode)
            settings = self.db.get_settings()
            mode = settings.get("bot_mode", "retail")
            system_prompt = REAL_ESTATE_SYSTEM_PROMPT if mode == "real_estate" else RETAIL_SYSTEM_PROMPT
            logger.info(f"📋 Using hardcoded {mode} prompt (no custom config found)")
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Load conversation history from database
        history = self.db.get_conversation_history(business_id, phone_number)
        
        if history:
            logger.info(f"📂 Loaded {len(history)} messages from history for: {phone_number}")
            for msg in history:
                role = msg.get("role", "user")
                # Groq uses "assistant" instead of "model"
                if role == "model":
                    role = "assistant"
                parts = msg.get("parts", [])
                text = parts[0] if parts else ""
                messages.append({"role": role, "content": text})
        else:
            logger.info(f"📱 New conversation started for: {phone_number}")
        
        # Add the new user message
        messages.append({"role": "user", "content": new_message})
        
        return messages
    
    async def generate_response(
        self,
        business_id: str,
        phone_number: str,
        user_message: str
    ) -> Optional[str]:
        """
        Generate an AI response for a user message.
        Both user message and AI response are persisted to the database.
        """
        try:
            logger.info(f"💬 Generating response for {phone_number}: {user_message[:50]}...")
            
            # Save the user's message to database
            self.db.save_message(business_id, phone_number, "user", user_message)
            
            # Build messages with history
            messages = self._build_messages(business_id, phone_number, user_message)
            
            # Generate response using Groq
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=300,
            )
            
            # Extract the response text
            ai_response = response.choices[0].message.content
            
            # Save the AI response to database
            self.db.save_message(business_id, phone_number, "model", ai_response)
            
            logger.info(f"✅ Response generated and saved for {phone_number}")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {str(e)}")
            
            # Return a short, human-like fallback message
            return "sorry, i'm having a small issue on my end. please send that again"
    
    def clear_conversation(self, business_id: str, phone_number: str) -> bool:
        """Clear the conversation history for a specific user."""
        return self.db.clear_conversation(business_id, phone_number)
    
    def get_conversation_count(self, business_id: str = None) -> int:
        """Get the total number of unique conversations in the database."""
        return self.db.get_conversation_count(business_id)


# Create a singleton instance to be imported by other modules
ai_engine = GroqAIEngine()


# =============================================================================
# STANDALONE TESTING
# =============================================================================
if __name__ == "__main__":
    import asyncio
    
    async def test_ai_engine():
        """Test the AI engine with sample messages."""
        test_messages = [
            "Hello, I'm interested in your drinks",
            "How much is hennessy?",
            "give me 2 bottles"
        ]
        
        test_phone = "+2348012345678"
        
        for message in test_messages:
            print(f"\n👤 User: {message}")
            response = await ai_engine.generate_response(test_phone, message)
            print(f"\n🤖 Temitope's AI: {response}")
            print("-" * 50)
    
    asyncio.run(test_ai_engine())
