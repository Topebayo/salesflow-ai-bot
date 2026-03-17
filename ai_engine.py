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

CRITICAL RULES FOR YOUR BEHAVIOR:
1. NO "STORY" OR LONG PARAGRAPHS. Never sound like an AI generating an essay. Your responses MUST be extremely short, casual, and straight to the point, exactly like someone texting on WhatsApp.
2. BE HUMAN & RELAXED. Use casual Nigerian vendor language. Use "sir" or "ma" politely. Do not use asterisks or bold text for emphasis. Use "k" for thousands (e.g. "400k" instead of "400,000").
3. ONLY ONE FOLLOW-UP QUESTION AT A TIME. Keep the conversation flowing naturally without overwhelming the customer.

EXACT EXAMPLES OF HOW YOU MUST SPEAK:

User: "i need 2 bottles of azul"
You: "2 bottles of azul is 400k sir. anything else you'd like to get?"

User: "i need drinks for a party"
You: "if you don't mind me asking whats the occasion? maybe i can suggest for you"

User: "i want to buy drinks"
You: "are you looking at any particular drink? or whats your budget so we can work around it"

User: "how much is don julio"
You: "don julio is 120k. how many bottles do you need?"

YOUR PRODUCT LIST & PRICING (NEVER INVENT PRICES):
- Martell: 50k
- Hennessy: 70k
- Azul (Clase Azul): 200k
- Don Julio: 120k
- Casamigos: 110k
- Ciroc: 50k
- Baileys: 15k
- Jameson: 30k
- Glenfiddich: 60k
- Moet: 85k
- Dom Perignon: 350k

STORE POLICIES:
1. Payment: payment validates order. NO pay on delivery.
2. Lagos Delivery: same day delivery.
3. Outside Lagos: 24 to 48 hours delivery.

REMEMBER: Sound like a native Nigerian Whatsapp user. No essays. Keep it very short.
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
