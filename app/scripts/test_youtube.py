#!/usr/bin/env python3
"""
Test YouTube API connection and functionality
"""

from app.core.config import settings
from app.services.context_service import ContextResearchService
import asyncio

async def test_youtube_api():
    """Test YouTube API key and functionality"""
    
    print("🎥 Testing YouTube API Configuration...")
    print(f"API Key configured: {bool(settings.youtube_api_key)}")
    
    if settings.youtube_api_key:
        print(f"API Key (first 20 chars): {settings.youtube_api_key[:20]}...")
        print(f"API Key (last 10 chars): ...{settings.youtube_api_key[-10:]}")
    else:
        print("❌ No YouTube API key found")
        return False
    
    print("\n🧪 Testing YouTube API call...")
    
    try:
        service = ContextResearchService()
        
        # Test with a simple search
        test_query = "Python programming tutorial"
        print(f"Test query: {test_query}")
        print("Searching YouTube...")
        
        results = await service._fetch_youtube_results(test_query, 3)
        
        if results:
            print(f"\n✅ Success! Found {len(results)} videos:")
            
            for i, video in enumerate(results, 1):
                print(f"\n--- Video {i} ---")
                print(f"Title: {video.get('title', 'N/A')}")
                print(f"Channel: {video.get('channel', 'N/A')}")
                print(f"Views: {video.get('view_count', 'N/A')}")
                print(f"URL: {video.get('url', 'N/A')}")
                
            return True
        else:
            print("❌ No results returned (but no error)")
            return False
            
    except Exception as e:
        print(f"❌ YouTube API test failed: {e}")
        
        # Check for common error types
        error_str = str(e).lower()
        if "api key" in error_str or "invalid" in error_str:
            print("💡 The API key appears to be invalid. Please check:")
            print("   1. Key is copied correctly (no extra spaces)")
            print("   2. YouTube Data API v3 is enabled in Google Cloud Console")
            print("   3. Key has proper permissions for YouTube Data API")
            print("   4. Get a new key from: https://console.cloud.google.com/apis/credentials")
        elif "quota" in error_str or "exceeded" in error_str:
            print("💡 Quota exceeded. Check your Google Cloud Console usage limits.")
        elif "forbidden" in error_str or "403" in error_str:
            print("💡 Access forbidden. Ensure YouTube Data API v3 is enabled.")
        else:
            print(f"💡 Unexpected error: {e}")
            
        return False

def main():
    """Run the YouTube API test"""
    success = asyncio.run(test_youtube_api())
    
    if success:
        print("\n🎉 YouTube API is working correctly!")
        print("\n📊 Benefits:")
        print("   ✅ Video context for Reddit posts")
        print("   ✅ Enhanced AI response quality")
        print("   ✅ Richer research insights")
    else:
        print("\n❌ YouTube API test failed.")
        print("\n⚠️  Impact:")
        print("   • Context research will be limited to Google search only")
        print("   • AI responses may be less informed")
        print("   • No video insights in generated content")

if __name__ == "__main__":
    main()