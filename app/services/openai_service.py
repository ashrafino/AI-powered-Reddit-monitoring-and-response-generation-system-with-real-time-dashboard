from typing import List, Dict, Optional
import logging
from openai import OpenAI

from app.core.config import settings
from app.services.quality_scoring import ResponseQualityScorer
from app.services.context_service import ContextResearchService, ContextData

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None


async def generate_reddit_replies_with_research(
    post_title: str,
    post_content: str = "",
    num: int = 3,
    brand_voice: Optional[str] = None,
    client_preferences: Optional[Dict] = None,
    enable_research: bool = True
) -> Dict:
    """
    Generate Reddit replies with context research, quality scoring and brand voice customization
    Returns dict with responses, context data, and metadata
    """
    if not client:
        return {
            "responses": [
                {
                    "content": "[OpenAI not configured] Suggestion 1",
                    "score": 0,
                    "quality_breakdown": {},
                    "feedback": ["OpenAI API not configured"],
                    "grade": "F"
                },
                {
                    "content": "[OpenAI not configured] Suggestion 2", 
                    "score": 0,
                    "quality_breakdown": {},
                    "feedback": ["OpenAI API not configured"],
                    "grade": "F"
                }
            ],
            "context_data": None,
            "research_enabled": False,
            "generation_metadata": {
                "model": "none",
                "research_quality": 0.0,
                "total_responses_generated": 0
            }
        }

    context_data = None
    context_text = ""
    
    # Perform context research if enabled
    if enable_research:
        try:
            research_service = ContextResearchService()
            context_data = await research_service.research_post_context(
                post_title, post_content, max_google_results=5, max_youtube_results=3
            )
            context_text = context_data.synthesized_context
            logger.info(f"Context research completed with quality: {context_data.research_quality}")
        except Exception as e:
            logger.error(f"Context research failed: {e}")
            context_text = "Context research unavailable."

    # Build system prompt with brand voice
    system_prompt = build_system_prompt(brand_voice, client_preferences)
    
    # Build user prompt with researched context
    full_prompt = f"{post_title}\n{post_content}".strip()
    user_prompt = build_user_prompt(full_prompt, context_text, num)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            n=1,
            temperature=0.8,
            max_tokens=800,
        )
        
        text = resp.choices[0].message.content or ""
        raw_suggestions = [s.strip("- •\n ") for s in text.split("\n") if s.strip()]
        
        # Score each response
        scorer = ResponseQualityScorer()
        scored_responses = []
        
        for i, suggestion in enumerate(raw_suggestions):
            if len(suggestion) < 10:  # Skip very short responses
                continue
                
            quality_data = scorer.score_response(suggestion, context_text, post_title)
            
            scored_responses.append({
                "content": suggestion,
                "score": int(quality_data['overall_score']),
                "quality_breakdown": quality_data['breakdown'],
                "feedback": quality_data['feedback'],
                "grade": quality_data['grade']
            })
        
        # Sort by quality score (highest first)
        scored_responses.sort(key=lambda x: x['score'], reverse=True)
        
        # Ensure we have at least num responses
        while len(scored_responses) < num:
            scored_responses.append({
                "content": f"[Generated response {len(scored_responses) + 1}]",
                "score": 50,
                "quality_breakdown": {
                    'relevance': 50, 'readability': 50, 'authenticity': 50,
                    'helpfulness': 50, 'compliance': 50
                },
                "feedback": ["Fallback response - insufficient content generated"],
                "grade": "D"
            })
        
        return {
            "responses": scored_responses[:num],
            "context_data": context_data,
            "research_enabled": enable_research,
            "generation_metadata": {
                "model": "gpt-4o-mini",
                "research_quality": context_data.research_quality if context_data else 0.0,
                "total_responses_generated": len(raw_suggestions),
                "context_sources": len(context_data.sources) if context_data else 0
            }
        }
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        # Fallback responses with error info
        return {
            "responses": [
                {
                    "content": f"[Error generating response: {str(e)}]",
                    "score": 0,
                    "quality_breakdown": {
                        'relevance': 0, 'readability': 0, 'authenticity': 0,
                        'helpfulness': 0, 'compliance': 0
                    },
                    "feedback": [f"OpenAI API error: {str(e)}"],
                    "grade": "F"
                }
            ],
            "context_data": context_data,
            "research_enabled": enable_research,
            "generation_metadata": {
                "model": "gpt-4o-mini",
                "research_quality": context_data.research_quality if context_data else 0.0,
                "total_responses_generated": 0,
                "error": str(e)
            }
        }


def generate_reddit_replies(
    prompt: str, 
    context: str | None = None, 
    num: int = 3,
    brand_voice: Optional[str] = None,
    client_preferences: Optional[Dict] = None
) -> List[Dict]:
    """
    Legacy synchronous function for backward compatibility
    Generate Reddit replies with quality scoring and brand voice customization
    Returns list of dicts with content, score, and quality breakdown
    """
    if not client:
        return [
            {
                "content": "[OpenAI not configured] Suggestion 1",
                "score": 0,
                "quality_breakdown": {},
                "feedback": ["OpenAI API not configured"],
                "grade": "F"
            },
            {
                "content": "[OpenAI not configured] Suggestion 2", 
                "score": 0,
                "quality_breakdown": {},
                "feedback": ["OpenAI API not configured"],
                "grade": "F"
            }
        ]

    # Build system prompt with brand voice
    system_prompt = build_system_prompt(brand_voice, client_preferences)
    
    # Build user prompt with context
    user_prompt = build_user_prompt(prompt, context, num)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            n=1,
            temperature=0.8,
            max_tokens=800,
        )
        
        text = resp.choices[0].message.content or ""
        raw_suggestions = [s.strip("- •\n ") for s in text.split("\n") if s.strip()]
        
        # Score each response
        scorer = ResponseQualityScorer()
        scored_responses = []
        
        for i, suggestion in enumerate(raw_suggestions[:num]):
            if len(suggestion) < 10:  # Skip very short responses
                continue
                
            quality_data = scorer.score_response(suggestion, context, prompt)
            
            scored_responses.append({
                "content": suggestion,
                "score": int(quality_data['overall_score']),
                "quality_breakdown": quality_data['breakdown'],
                "feedback": quality_data['feedback'],
                "grade": quality_data['grade']
            })
        
        # Sort by quality score (highest first)
        scored_responses.sort(key=lambda x: x['score'], reverse=True)
        
        # Ensure we have at least num responses
        while len(scored_responses) < num:
            scored_responses.append({
                "content": f"[Generated response {len(scored_responses) + 1}]",
                "score": 50,
                "quality_breakdown": {
                    'relevance': 50, 'readability': 50, 'authenticity': 50,
                    'helpfulness': 50, 'compliance': 50
                },
                "feedback": ["Fallback response"],
                "grade": "D"
            })
        
        return scored_responses[:num]
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        # Fallback responses with error info
        return [
            {
                "content": f"[Error generating response: {str(e)}]",
                "score": 0,
                "quality_breakdown": {
                    'relevance': 0, 'readability': 0, 'authenticity': 0,
                    'helpfulness': 0, 'compliance': 0
                },
                "feedback": [f"OpenAI API error: {str(e)}"],
                "grade": "F"
            }
        ]


def build_system_prompt(brand_voice: Optional[str] = None, client_preferences: Optional[Dict] = None) -> str:
    """Build customized system prompt based on brand voice and preferences"""
    
    base_prompt = """You are a helpful Reddit commenter who writes authentic, human-like responses. 

Key guidelines:
- Use natural, conversational language
- Be helpful and constructive
- Follow Reddit etiquette and tone
- Avoid promotional or spam-like content
- Keep responses concise but informative
- Use personal experience when appropriate
- Be respectful and inclusive"""

    if brand_voice:
        base_prompt += f"\n\nBrand voice: {brand_voice}"
    
    if client_preferences:
        if client_preferences.get('tone'):
            base_prompt += f"\nTone: {client_preferences['tone']}"
        if client_preferences.get('expertise_areas'):
            areas = ', '.join(client_preferences['expertise_areas'])
            base_prompt += f"\nExpertise areas: {areas}"
        if client_preferences.get('avoid_topics'):
            topics = ', '.join(client_preferences['avoid_topics'])
            base_prompt += f"\nAvoid discussing: {topics}"
    
    return base_prompt


def build_user_prompt(prompt: str, context: str | None = None, num: int = 3) -> str:
    """Build user prompt with context and instructions"""
    
    user_prompt = f"Reddit Post: {prompt}"
    
    if context:
        user_prompt += f"\n\nAdditional Context:\n{context}"
    
    user_prompt += f"""

Generate {num} distinct, high-quality Reddit comment responses. Each response should:
1. Be relevant to the original post
2. Sound natural and human-like
3. Provide value (helpful information, perspective, or support)
4. Follow Reddit community guidelines
5. Be appropriately sized (20-150 words typically)

Format each response on a separate line starting with a dash (-)."""

    return user_prompt


def generate_brand_voice_suggestions(industry: str, tone_preferences: List[str]) -> Dict[str, str]:
    """Generate brand voice suggestions for different industries"""
    
    industry_voices = {
        "technology": "Technical but approachable. Use industry terms when appropriate but explain complex concepts clearly. Focus on practical solutions and real-world applications.",
        "healthcare": "Professional and trustworthy. Emphasize safety and evidence-based information. Always recommend consulting healthcare professionals for medical advice.",
        "finance": "Professional and conservative. Focus on education and general principles. Always include disclaimers about seeking professional financial advice.",
        "education": "Knowledgeable and encouraging. Break down complex topics into understandable parts. Encourage learning and curiosity.",
        "retail": "Friendly and customer-focused. Emphasize value and customer satisfaction. Be helpful with product recommendations and comparisons.",
        "food": "Enthusiastic and descriptive. Share experiences and recommendations. Focus on taste, quality, and value.",
        "travel": "Adventurous and informative. Share experiences and practical tips. Focus on value and unique experiences.",
        "fitness": "Motivational and supportive. Emphasize safety and gradual progress. Encourage healthy habits and consistency."
    }
    
    tone_modifiers = {
        "casual": "Use relaxed, conversational language with contractions and informal expressions.",
        "professional": "Maintain a polished, business-appropriate tone while staying approachable.",
        "friendly": "Be warm and welcoming. Use inclusive language and show genuine interest in helping.",
        "expert": "Demonstrate deep knowledge while remaining accessible. Back up claims with experience or sources.",
        "humorous": "Use appropriate humor when suitable. Keep it light and positive.",
        "supportive": "Be encouraging and empathetic. Acknowledge challenges and offer constructive help."
    }
    
    base_voice = industry_voices.get(industry.lower(), "Professional and helpful. Focus on providing value and building trust with authentic, informative responses.")
    
    if tone_preferences:
        tone_additions = [tone_modifiers.get(tone.lower(), "") for tone in tone_preferences]
        tone_text = " ".join(filter(None, tone_additions))
        if tone_text:
            base_voice += f" {tone_text}"
    
    return {
        "suggested_voice": base_voice,
        "industry_examples": industry_voices,
        "tone_options": tone_modifiers
    }



