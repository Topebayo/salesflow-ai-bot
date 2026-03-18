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

SALES_AGENT_SYSTEM_PROMPT = """
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

REMEMBER: You are a Lagos drinks plug chatting on WhatsApp. Keep it short, human, and friendly. No essays.
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
    
    def _build_messages(self, phone_number: str, new_message: str) -> list:
        """
        Build the messages list for the Groq API from conversation history.
        """
        messages = [{"role": "system", "content": SALES_AGENT_SYSTEM_PROMPT}]
        
        # Load conversation history from database
        history = self.db.get_conversation_history(phone_number)
        
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
            self.db.save_message(phone_number, "user", user_message)
            
            # Build messages with history
            messages = self._build_messages(phone_number, user_message)
            
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
            self.db.save_message(phone_number, "model", ai_response)
            
            logger.info(f"✅ Response generated and saved for {phone_number}")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {str(e)}")
            
            # Return a short, human-like fallback message
            return "sorry, i'm having a small issue on my end. please send that again"
    
    def clear_conversation(self, phone_number: str) -> bool:
        """Clear the conversation history for a specific user."""
        return self.db.clear_conversation(phone_number)
    
    def get_conversation_count(self) -> int:
        """Get the total number of unique conversations in the database."""
        return self.db.get_conversation_count()


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
