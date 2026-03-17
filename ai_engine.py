"""
=============================================================================
AI ENGINE MODULE - GEMINI 1.5 FLASH INTEGRATION
=============================================================================
This module handles all AI-related functionality using Google's Gemini 1.5 Flash.
It includes a robust system prompt designed for a high-performing Nigerian
Sales Closer that drives conversions.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# SYSTEM PROMPT - NIGERIAN SALES CLOSER PERSONA
# =============================================================================
# This prompt defines the AI's personality, sales methodology, and behavior.
# It's designed to be persuasive, professional, and culturally relevant.

SALES_AGENT_SYSTEM_PROMPT = """
You are **Temitope's AI**, a world-class AI Sales Agent representing our premium liquor delivery service based in Lagos, Nigeria. You are a warm, professional, and highly persuasive Nigerian sales closer with deep expertise in selling premium spirits and drinks.

## YOUR CORE IDENTITY & BUSINESS KNOWLEDGE:
- You speak with confidence, warmth, and authentic Nigerian flair.
- You understand the Nigerian nightlife, party culture, and how to recommend the perfect drink for any vibe.
- You are located in **Lagos, Nigeria**.

## YOUR PRODUCT LIST & PRICING:
You exclusively sell the following premium drinks at these fixed prices. NEVER invent prices or offer products not on this list.

**Cognac:**
- Martell: ₦50,000
- Hennessy: ₦70,000

**Tequila:**
- Azul (Clase Azul): ₦200,000
- Don Julio: ₦120,000
- Casamigos: ₦110,000

**Vodka & Cream:**
- Ciroc: ₦50,000
- Baileys: ₦15,000

**Whiskey & Champagne:**
- Jameson: ₦30,000
- Glenfiddich: ₦60,000
- Moët: ₦85,000
- Dom Pérignon: ₦350,000

## STORE POLICIES (VERY IMPORTANT):
1. **Payment:** "Payment validates order." You must emphasize that payment must be made upfront to confirm the order. NO pay-on-delivery.
2. **Delivery in Lagos:** Same-day delivery! 🚀
3. **Delivery Outside Lagos:** Takes 24 to 48 hours for delivery. 📦

## YOUR SALES METHODOLOGY:

### 1. WARM GREETING
- Example: "Hello! 👋 I'm Temitope's AI, your premium drinks plug! What are we celebrating today, or what can I get for you?"

### 2. DISCOVERY & RECOMMENDATIONS
- If they ask for recommendations, ask about the occasion or their budget.
- E.g., "If you are celebrating something huge, that Azul (₦200k) or Dom Pérignon (₦350k) is the ultimate flex! But if you just want a chill evening, the Baileys (₦15k) or Jameson (₦30k) is perfect."

### 3. CLOSING THE SALE (Order Confirmation)
- Once they select their drinks, total up the price.
- Ask for their delivery address to confirm if it's inside or outside Lagos.
- State clearly: "Just a quick reminder: payment validates the order. Once your transfer is confirmed, I'll dispatch it immediately!"

## WHAT YOU SHOULD NEVER DO:
❌ Never invent products or make up prices. Stick strictly to the price list.
❌ Never promise pay-on-delivery.
❌ Never offer unauthorized discounts.
"""


class GeminiAIEngine:
    """
    AI Engine class that handles all interactions with Google's Gemini 2.5 Flash.
    Maintains conversation context using persistent SQLite storage via database.py.
    Conversations survive server restarts.
    """
    
    def __init__(self):
        """
        Initialize the Gemini AI Engine with API configuration and database.
        """
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables!")
            raise ValueError("GEMINI_API_KEY is required. Please set it in your .env file.")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model with Gemini 2.5 Flash
        # Using 2.5 Flash for optimal speed and cost-effectiveness
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SALES_AGENT_SYSTEM_PROMPT
        )
        
        # Import database for persistent storage
        from database import db
        self.db = db
        
        logger.info("✅ Gemini AI Engine initialized with persistent storage!")
    
    def _get_or_create_chat(self, phone_number: str):
        """
        Get existing chat history from database or create a new conversation.
        
        Args:
            phone_number: The user's WhatsApp phone number (unique identifier)
            
        Returns:
            Chat session for the user, loaded with conversation history from database
        """
        # Load conversation history from persistent storage
        history = self.db.get_conversation_history(phone_number)
        
        if not history:
            logger.info(f"📱 New conversation started for: {phone_number}")
        else:
            logger.info(f"📂 Loaded {len(history)} messages from history for: {phone_number}")
        
        # Create chat with history from database
        chat = self.model.start_chat(history=history)
        return chat
    
    async def generate_response(
        self,
        phone_number: str,
        user_message: str
    ) -> Optional[str]:
        """
        Generate an AI response for a user message.
        Both user message and AI response are persisted to the database.
        
        Args:
            phone_number: The sender's WhatsApp phone number
            user_message: The message content from the user
            
        Returns:
            AI-generated response string, or None if generation fails
        """
        try:
            logger.info(f"💬 Generating response for {phone_number}: {user_message[:50]}...")
            
            # Save the user's message to database
            self.db.save_message(phone_number, "user", user_message)
            
            # Get or create chat session for this user (loads full history)
            chat = self._get_or_create_chat(phone_number)
            
            # Generate response using Gemini
            response = chat.send_message(user_message)
            
            # Extract the response text
            ai_response = response.text
            
            # Save the AI response to database
            self.db.save_message(phone_number, "model", ai_response)
            
            logger.info(f"✅ Response generated and saved for {phone_number}")
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {str(e)}")
            
            # Return a graceful fallback message
            return (
                "I apologize, but I'm experiencing a brief technical hiccup. 🙏\n\n"
                "Please give me a moment and try again. "
                "Your inquiry is important to us, and I'll be right back to assist you!\n\n"
                "If this persists, you can also reach us directly at [your contact info]."
            )
    
    def clear_conversation(self, phone_number: str) -> bool:
        """
        Clear the conversation history for a specific user.
        Removes all messages from the database for this phone number.
        
        Args:
            phone_number: The user's WhatsApp phone number
            
        Returns:
            True if conversation was cleared, False if no conversation existed
        """
        return self.db.clear_conversation(phone_number)
    
    def get_conversation_count(self) -> int:
        """
        Get the total number of unique conversations in the database.
        
        Returns:
            Number of unique conversations
        """
        return self.db.get_conversation_count()


# Create a singleton instance to be imported by other modules
ai_engine = GeminiAIEngine()


# =============================================================================
# STANDALONE TESTING
# =============================================================================
if __name__ == "__main__":
    import asyncio
    
    async def test_ai_engine():
        """Test the AI engine with sample messages."""
        test_messages = [
            "Hello, I'm interested in your services",
            "How much does it cost?",
            "That sounds good, how do I get started?"
        ]
        
        test_phone = "+2348012345678"
        
        for message in test_messages:
            print(f"\n👤 User: {message}")
            response = await ai_engine.generate_response(test_phone, message)
            print(f"\n🤖 Temitope's AI: {response}")
            print("-" * 50)
    
    asyncio.run(test_ai_engine())
