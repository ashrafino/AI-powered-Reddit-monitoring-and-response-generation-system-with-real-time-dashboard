#!/usr/bin/env python3
"""
Test OpenAI API connection and functionality
"""

import os
from app.core.config import settings
from app.services.openai_service import generate_reddit_replies

def test_openai_connection():
    """Test OpenAI API key and functionality"""
    
    print("🔑 Testing OpenAI API Configuration...")
    print(f"API Key configured: {bool(settings.openai_api_key)}")
    
    if settings.openai_api_key:
        print(f"API Key (first 20 chars): {settings.openai_api_key[:20]}...")
        print(f"API Key (last 10 chars): ...{settings.openai_api_key[-10:]}")
    else:
        print("❌ No OpenAI API key found")
        return False
    
    print("\n🧪 Testing OpenAI API call...")
    
    try:
        # Test with a simple Reddit post
        test_prompt = "What's the best programming language for beginners?"
        test_context = "Discussion about learning programming"
        
        print(f"Test prompt: {test_prompt}")
        print("Generating responses...")
        
        responses = generate_reddit_replies(
            prompt=test_prompt,
            context=test_context,
            num=2
        )
        
        print(f"\n✅ Success! Generated {len(responses)} responses:")
        
        for i, response in enumerate(responses, 1):
            print(f"\n--- Response {i} ---")
            print(f"Content: {response['content'][:100]}...")
            print(f"Score: {response['score']}")
            print(f"Grade: {response['grade']}")
            
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        
        # Check for common error types
        error_str = str(e).lower()
        if "invalid api key" in error_str or "incorrect api key" in error_str:
            print("💡 The API key appears to be invalid. Please check:")
            print("   1. Key is copied correctly (no extra spaces)")
            print("   2. Key has proper permissions")
            print("   3. Account has available credits")
            print("   4. Get a new key from: https://platform.openai.com/account/api-keys")
        elif "quota" in error_str or "billing" in error_str:
            print("💡 Billing/quota issue. Please check your OpenAI account billing.")
        elif "rate limit" in error_str:
            print("💡 Rate limit exceeded. Wait a moment and try again.")
        else:
            print(f"💡 Unexpected error: {e}")
            
        return False

if __name__ == "__main__":
    success = test_openai_connection()
    if success:
        print("\n🎉 OpenAI API is working correctly!")
    else:
        print("\n❌ OpenAI API test failed. Please fix the issues above.")