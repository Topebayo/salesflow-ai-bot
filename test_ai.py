"""
Test script for the AI Sales Agent
"""
import asyncio
import sys

# Fix Windows encoding issues
sys.stdout.reconfigure(encoding='utf-8')

from ai_engine import ai_engine

async def test_conversation():
    """Run a sample sales conversation"""
    
    phone = "+2348012345678"
    
    # Test messages simulating a real sales conversation
    messages = [
        "Hi, I saw your ad online",
        "What services do you offer?",
        "How much does it cost?"
    ]
    
    print("=" * 60)
    print("🤖 WHATSAPP AI SALES AGENT - TEST CONVERSATION")
    print("=" * 60)
    print()
    
    for msg in messages:
        print(f"👤 CUSTOMER: {msg}")
        print("-" * 40)
        
        response = await ai_engine.generate_response(phone, msg)
        
        print(f"🤖 ADAEZE (AI):")
        print(response)
        print()
        print("=" * 60)
        print()

if __name__ == "__main__":
    asyncio.run(test_conversation())
