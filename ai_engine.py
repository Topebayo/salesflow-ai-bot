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
from groq import AsyncGroq

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# SYSTEM PROMPT - NIGERIAN DRINKS VENDOR PERSONA
# =============================================================================

RETAIL_SYSTEM_PROMPT = """
You are Temitope's AI, a human-like vendor selling premium sneakers and apparel in Lagos, Nigeria chatting on WhatsApp.

CRITICAL RULES:
1. NO LONG PARAGRAPHS. Keep responses extremely short and casual, like a real person texting on WhatsApp.
2. BE HUMAN. Use casual Nigerian vendor language. Say "sir" or "ma" politely. Use "k" for thousands (e.g. "40k"). No asterisks or bold text.
3. ONE FOLLOW-UP QUESTION AT A TIME. Don't overwhelm the customer.
4. ALWAYS try to upsell gently. After they pick a product, suggest something that pairs well (e.g. socks, sneaker cleaner, caps).

CONVERSATION EXAMPLES (match this exact vibe):

User: "i need 2 sneakers"
You: "nice one sir. what size and which brand are you looking at?"

User: "do you have hoodies"
You: "yes ma! we have premium oversized hoodies. what size do you wear?"

User: "how much is the jordan 4"
You: "jordan 4 is 85k sir. do you want it in blue or black?"

User: "thats all"
You: "alright sir, your total is [amount]. kindly send payment to OPay - 8137048851 (Temitope). once payment is confirmed your order gets dispatched immediately"

User: "do you deliver"
You: "yes sir! same day delivery if you're in Lagos. outside Lagos is 24-48 hours. where are you located?"

User: "can i pay when it arrives"
You: "sorry sir, payment validates the order. we don't do pay on delivery. but once your transfer drops, we dispatch immediately"

User: "do you have proof / are you legit"
You: "yes sir you can check our instagram @salesflow_apparel for reviews and past deliveries"

User: "give me discount na"
You: "lol the prices are already very fair sir. but if you're buying 2 pairs and above i can throw in free shipping for you"

User: "what can i get for 50k"
You: "for 50k you can get a premium tee (20k) + luxury slides (30k), or our cargo pants (25k) + a hoodie (25k). which combo do you prefer?"

FULL PRODUCT LIST & PRICING (NEVER INVENT PRICES OR PRODUCTS):

SNEAKERS & SHOES:
- Air Force 1: 50k
- Jordan 4: 85k
- Yeezy Boost: 90k
- Luxury Slides: 30k

APPAREL (CLOTHING):
- Premium Tee: 20k
- Oversized Hoodie: 25k
- Cargo Pants: 25k
- Designer Cap: 15k

EXTRAS & ADD-ONS:
- Premium Socks (3-pack): 5k
- Sneaker Cleaner Kit: 8k
- Gift Box Packaging: 3k

If someone buys 2+ pairs of sneakers, offer free shipping.

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

INSTAGRAM: @salesflow_apparel (direct customers here if they want proof, reviews, or to see past deliveries)

UPSELLING TIPS (use naturally, dont force):
- If they order sneakers, ask "should i add a cleaner kit or premium socks?"
- If they order a hoodie, suggest "we also have matching cargo pants that go well with it"
- If budget allows, gently suggest upgrading (e.g. "if you want to level up, the jordan 4 is also very popular at 85k")

HANDOFF PROTOCOL:
If a customer explicitly asks to speak to a human, customer service, or the owner, you MUST end your response exactly with this secret token: [HANDOFF_TRIGGERED]
Example: "no problem, i have notified the boss. someone will reply shortly! [HANDOFF_TRIGGERED]"

REMEMBER: You are a Lagos apparel plug chatting on WhatsApp. Keep it short, human, and friendly. No essays.
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
        
        # Initialize the Groq client as asynchronous
        self.client = AsyncGroq(api_key=self.api_key)
        self.model_name = "llama-3.1-8b-instant"
        
        # Import database for persistent storage
        from database import db
        self.db = db
        
        logger.info("✅ Groq AI Engine initialized with persistent storage!")
    
    def _build_custom_prompt(self, config: dict, business_id: str = None, user_message: str = "") -> str:
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
5. Never misspell or alter payment gateway names. Always write OPay as 'OPay' (never write it as 'Ola pay' or similar).
"""

        if bot_mode == "real_estate":
            prompt += """
REAL ESTATE QUALIFICATION FLOW:
1. When chatting with a new customer, dynamically qualify their needs by asking for:
   - Their budget range (e.g. 50 Million, 100M, etc.)
   - Their preferred location or neighborhood
2. Ask about their budget or location naturally and conversationally. Do not sound like a robot.
3. When the customer tells you their budget or preferred location (or both), you MUST append a hidden qualification tag at the very end of your response using this exact format:
   [QUALIFY: budget=MIN-MAX, location=NAME]
   Examples:
   - If they say: "I have 50 million to 60 million and want to buy in Lekki", append: [QUALIFY: budget=50M-60M, location=Lekki]
   - If they only state location: "I want a flat in Ikeja", append: [QUALIFY: budget=, location=Ikeja]
   - If they only state budget: "My budget is 80 Million", append: [QUALIFY: budget=80M-80M, location=]
   Always keep the values simple (e.g., use 'M' for Millions). Ensure you include the brackets [ ] and the exact 'QUALIFY' keyword. This tag is hidden from the customer but helps update the agent dashboard.
"""

        if greeting:
            prompt += f"""
GREETING: When a customer says "hi", "hello", or starts a new conversation, reply with something like: "{greeting}"
"""

        if description:
            prompt += f"""
ABOUT THE BUSINESS: {description}
"""

        auto_learned_knowledge = config.get("auto_learned_knowledge", "")
        if auto_learned_knowledge:
            prompt += f"""
ADDITIONAL BUSINESS KNOWLEDGE & FAQS (AUTO-LEARNT FROM HISTORICAL CHATS):
{auto_learned_knowledge}
"""

        # Fetch products from database if business_id is provided
        db_products = []
        if business_id:
            db_products = self.db.get_available_products(business_id)

        if db_products:
            # If there are many products, filter them based on keywords in user message / context to prevent 413 Payload Too Large / TPM limit exceeded.
            if len(db_products) > 15:
                search_text = user_message.lower()
                
                # Known locations in our catalog
                locations_list = [
                    "lagos", "abuja", "fct", "abia", "adamawa", "akwa ibom", "anambra", "bauchi", "bayelsa", 
                    "benue", "borno", "cross river", "delta", "ebonyi", "edo", "ekiti", "enugu", "gombe", 
                    "imo", "jigawa", "kaduna", "kano", "katsina", "kebbi", "kogi", "kwara", "nasarawa", 
                    "niger", "ogun", "ondo", "osun", "oyo", "plateau", "rivers", "sokoto", "taraba", 
                    "yobe", "zamfara", "ibadan", "lekki", "ikeja", "bodija"
                ]

                # Known categories
                categories_list = [
                    "duplex", "mansion", "bungalow", "commercial", "land", "apartment"
                ]
                
                # Identify which locations and categories are mentioned in the query
                matched_locations = [loc for loc in locations_list if loc in search_text]
                matched_categories = [cat for cat in categories_list if cat in search_text]
                
                # Also extract general words of length > 3 for broad matching
                words = [w.strip("?,.!:;()\"'") for w in search_text.split()]
                general_keywords = [w for w in words if len(w) > 3 and w not in matched_locations and w not in matched_categories]
                
                scored_products = []
                for p_item in db_products:
                    p_name = p_item['name'].lower()
                    p_desc = p_item.get('description', '').lower()
                    p_cat = p_item.get('category', '').lower()
                    p_text = f"{p_name} {p_desc} {p_cat}"
                    
                    score = 0
                    
                    # Location match (highest weight)
                    for loc in matched_locations:
                        if loc in p_text:
                            score += 10
                            
                    # Category match (medium weight)
                    for cat in matched_categories:
                        if cat in p_text or cat in p_cat:
                            score += 5
                            
                    # General word matches
                    for kw in general_keywords:
                        if kw in p_text:
                            score += 1
                            
                    if score > 0:
                        scored_products.append((p_item, score))
                        
                # Sort by score descending
                scored_products.sort(key=lambda x: x[1], reverse=True)
                
                filtered = [item[0] for item in scored_products]
                
                # Fallback to default list if not enough matches are found
                if len(filtered) < 5:
                    for p_item in db_products[:15]:
                        if p_item not in filtered:
                            filtered.append(p_item)
                            
                db_products = filtered[:15]
                
                # Append a hint for the LLM that more products exist in other locations
                prompt += f"""
NOTE: We have 185 properties across all 36 states in Nigeria (plus FCT Abuja). A subset matching the customer's query is listed below. If they ask about a different state, tell them we have 5 properties in that state and ask what type of property they are interested in.
"""

            # Build structured products prompt
            product_list_str = ""
            for p in db_products:
                try:
                    price_val = float(p.get('price')) if p.get('price') else 0
                    price_str = f" ₦{price_val:,.0f}" if price_val > 0 else " Price on request"
                except Exception:
                    price_str = f" ₦{p.get('price')}"
                category_str = f" [{p['category']}]" if p.get('category') else ""
                
                # Check for property specs in Real Estate mode
                if bot_mode == "real_estate":
                    specs = []
                    if p.get('property_type'): specs.append(f"Type: {p['property_type']}")
                    if p.get('bedrooms'): specs.append(f"{p['bedrooms']} Beds")
                    if p.get('bathrooms'): specs.append(f"{p['bathrooms']} Baths")
                    if p.get('location'): specs.append(f"Location: {p['location']}")
                    if p.get('virtual_tour_url'): specs.append(f"Virtual Tour: {p['virtual_tour_url']}")
                    specs_str = f" ({', '.join(specs)})" if specs else ""
                    desc_str = f" - {p.get('description', '')}{specs_str}"
                else:
                    desc_str = f" - {p.get('description', '')}"
                    
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
        else:
            prompt += """
PRODUCTS / SERVICES & PRICES:
(No products, properties, or services are currently configured in our catalog)

IMPORTANT: We currently have NO products, packages, properties, or services listed in our catalog. If the customer asks about packages, pricing, products, or services, politely explain that the catalog is currently being updated and ask them to check back shortly or let them know you can connect them with an agent. Under NO circumstances should you invent, make up, or hallucinate any packages, properties, items, or prices.
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
        # Load conversation history from database
        history = self.db.get_conversation_history(business_id, phone_number)
        
        # Build search context for product filtering (combines current message and recent history)
        history_text = ""
        if history:
            history_text = " ".join([msg["parts"][0] for msg in history if msg.get("parts")])
        search_context = new_message + " " + history_text

        # First, try to load custom prompt config from the business settings
        business_config = self.db.get_business_config(business_id)
        
        if business_config:
            # Business has configured their custom prompt — use it
            system_prompt = self._build_custom_prompt(business_config, business_id, search_context)
            logger.info(f"🎨 Using custom prompt for business: {business_config.get('name', 'Unknown')}")
        else:
            # Fallback to hardcoded prompts (legacy mode)
            settings = self.db.get_settings()
            mode = settings.get("bot_mode", "retail")
            system_prompt = REAL_ESTATE_SYSTEM_PROMPT if mode == "real_estate" else RETAIL_SYSTEM_PROMPT
            logger.info(f"📋 Using hardcoded {mode} prompt (no custom config found)")
        
        messages = [{"role": "system", "content": system_prompt}]
        
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
        user_message: str,
        save_user_message: bool = True,
        base64_image: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate an AI response for a user message.
        Both user message and AI response are persisted to the database.
        """
        try:
            logger.info(f"💬 Generating response for {phone_number}: {user_message[:50]}...")
            
            # Save the user's message to database if requested
            if save_user_message:
                self.db.save_message(business_id, phone_number, "user", user_message)
            
            # Build messages with history
            messages = self._build_messages(business_id, phone_number, user_message)
            
            # Generate response using AsyncGroq
            response = await self.client.chat.completions.create(
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

    async def generate_demo_response(self, user_message: str, history: list = None) -> str:
        """
        Generate an AI response for the public landing page demo chat.
        This represents SalesFlow AI's onboarding/product specialist.
        """
        system_prompt = """
You are SalesFlow AI Assistant, a friendly, extremely smart sales representative for SalesFlow AI.
SalesFlow AI is a SaaS platform that builds custom, human-like AI sales agents for businesses on WhatsApp.
Our AI agents handle customer chats 24/7, query the business's product database, automatically send product details/images, auto-detect orders, and handle human handoff.

PRICING DETAILS:
- Starter Plan: ₦75,000/month (Includes 1 AI agent, up to 500 conversations/month, and basic analytics).
- Growth Plan: ₦150,000/month (Includes 3 AI agents, up to 2,000 conversations/month, advanced database integrations, and custom branding).
- Enterprise Plan: Custom pricing (Unlimited agents/conversations, dedicated account manager, API integrations, and SLA).

CRITICAL RULES:
1. Be concise, friendly, and helpful. Keep responses to 2-3 sentences max.
2. If they ask about pricing, explain the starter and growth plans clearly.
3. If they ask how it works, explain that we connect their database and meta business WhatsApp, and setup takes 24 hours.
4. Invite them to register or fill out the contact form to get started.
5. Answer questions intelligently based on the capabilities of the system (Multi-tenant isolation, Supabase RLS security, multi-channel branding, order auto-detection).
"""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            # Append history if provided
            if history:
                for msg in history:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                    
            # If image is present, format content array for vision and use vision model
            if base64_image:
                user_content = [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
                messages.append({"role": "user", "content": user_content})
                model_to_use = "llama-3.2-11b-vision-preview"
                
                # Vision models often need higher token limits for detailed descriptions
                max_tokens = 500 
            else:
                messages.append({"role": "user", "content": user_message})
                model_to_use = self.model_name
                max_tokens = 300
            
            response = await self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in generate_demo_response: {e}")
            return "Thanks for asking! Our AI Sales Agent connects your database directly to WhatsApp to automate your sales 24/7. Please fill out the contact form below and we will get you set up within 24 hours!"


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
            "Hello, I'm interested in your sneakers",
            "How much is Jordan 4?",
            "do you deliver to lekki?"
        ]
        
        test_phone = "+2348012345678"
        dummy_biz_id = "00000000-0000-0000-0000-000000000000"
        
        for message in test_messages:
            print(f"\n👤 User: {message}")
            response = await ai_engine.generate_response(
                business_id=dummy_biz_id,
                phone_number=test_phone,
                user_message=message,
                save_user_message=False
            )
            print(f"\n🤖 Temitope's AI: {response}")
            print("-" * 50)
    
    asyncio.run(test_ai_engine())
