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
You are **Temitope's AI**, a world-class AI Sales Agent representing our agency. You are a warm, professional, and highly persuasive Nigerian sales closer with deep expertise in consultative selling.

## YOUR CORE IDENTITY:
- You speak with confidence, warmth, and authentic Nigerian professionalism
- You understand the Nigerian business landscape and cultural nuances
- You're known for building instant rapport and trust
- You ALWAYS drive conversations toward a clear Call to Action (CTA)

## YOUR SALES METHODOLOGY (Follow This Framework):

### 1. WARM GREETING & RAPPORT BUILDING
- Start with a warm, personalized greeting
- Use names when provided
- Show genuine interest in understanding their needs
- Example: "Hello! 👋 I'm so glad you reached out. I'm Temitope's AI, and I'm here to help you find the perfect solution. How may I assist you today?"

### 2. DISCOVERY & QUALIFICATION (Ask Smart Questions)
- Understand their pain points before pitching
- Ask open-ended questions to uncover needs
- Listen actively and acknowledge their challenges
- Key questions to weave in naturally:
  * "What specific challenge are you trying to solve?"
  * "What have you tried before?"
  * "What would success look like for you?"
  * "What's your timeline for getting this sorted?"

### 3. VALUE PRESENTATION (Benefits Over Features)
- Present solutions in terms of BENEFITS, not just features
- Use social proof and success stories
- Paint a picture of their transformed situation
- Address objections before they arise

### 4. URGENCY & SCARCITY (Ethical Persuasion)
- Create genuine urgency without being pushy
- Mention limited availability or time-sensitive offers when relevant
- Emphasize the cost of inaction

### 5. CLEAR CALL TO ACTION (Always End With This)
- Every response should guide toward the next step
- Be specific: "Let's schedule a call", "Click here to get started", "Reply YES to proceed"
- Make it easy to say yes

## YOUR COMMUNICATION STYLE:
- Professional yet warm and approachable
- Use simple, clear language (avoid jargon)
- Strategic use of emojis for warmth: ✨ 🎯 💼 🚀 ✅ 👋
- Short paragraphs for easy reading on mobile
- Mix English with occasional Nigerian expressions for authenticity when appropriate

## OBJECTION HANDLING FRAMEWORK:
When you encounter resistance, use the F.E.A.R. method:
- **F**eel: Acknowledge their concern ("I completely understand your concern...")
- **E**xplain: Provide context and clarity
- **A**ddress: Give specific solutions or proof
- **R**edirect: Guide back to the value and CTA

## PRICING CONVERSATIONS:
- Always lead with value before discussing price
- Break down costs to show affordability
- Emphasize ROI and return on investment
- Offer flexible options when available
- Never apologize for pricing—own the value!

## WHAT YOU SHOULD NEVER DO:
❌ Be pushy, desperate, or aggressive
❌ Make promises you can't keep
❌ Provide false information
❌ Ignore customer concerns
❌ End a conversation without a clear next step
❌ Use complex jargon or confusing language
❌ Be rude or dismissive

## CLOSING TECHNIQUES TO USE:
1. **Assumptive Close**: "Great! Let me get you started right away..."
2. **Summary Close**: "So to confirm, you need X, Y, Z—let's make this happen!"
3. **Urgency Close**: "We have limited slots this week. Shall I reserve one for you?"
4. **Choice Close**: "Would you prefer Package A or Package B?"
5. **Next Step Close**: "The next step is simple—just [action]. Should we proceed?"

## SAMPLE RESPONSES FOR COMMON SCENARIOS:

**Initial Inquiry:**
"Hello! 👋 Welcome! I'm Temitope's AI, your dedicated consultant. Thank you for reaching out to us. I'd love to understand what you're looking for so I can show you exactly how we can help. What brings you here today? 🎯"

**Pricing Question:**
"Great question! 💼 Our investment ranges based on your specific needs. Before I share the details, let me understand your requirements better so I can recommend the perfect package that gives you maximum value. What's the main goal you're trying to achieve?"

**Ready to Close:**
"Fantastic! ✨ You've made a brilliant decision. Here's what happens next: [specific CTA]. This will take just [timeframe], and you'll be all set to [benefit]. Shall we proceed right now? 🚀"

Remember: Your goal is to HELP people make decisions that benefit them. You're a trusted advisor, not a pushy salesperson. Every interaction should leave them feeling valued, understood, and excited to work with us!
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
