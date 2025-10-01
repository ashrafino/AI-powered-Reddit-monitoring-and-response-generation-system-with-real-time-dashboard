from typing import Dict, List, Optional, Tuple
import re
import logging
from datetime import datetime
from textstat import flesch_reading_ease, flesch_kincaid_grade, automated_readability_index
from app.core.config import settings

logger = logging.getLogger(__name__)


class QualityThresholds:
    """Quality thresholds for different scoring dimensions"""
    EXCELLENT = 90
    GOOD = 80
    ACCEPTABLE = 70
    NEEDS_IMPROVEMENT = 60
    POOR = 50
    
    # Dimension-specific thresholds
    RELEVANCE_MIN = 70
    READABILITY_MIN = 65
    AUTHENTICITY_MIN = 70
    HELPFULNESS_MIN = 65
    COMPLIANCE_MIN = 80  # Higher threshold for compliance
    
    # Overall quality thresholds
    AUTO_APPROVE = 85
    MANUAL_REVIEW = 60
    REJECT = 40


class ResponseQualityScorer:
    """Enhanced quality scoring system for AI-generated responses"""
    
    def __init__(self):
        self.thresholds = QualityThresholds()
        
        # Enhanced Reddit-specific quality indicators
        self.positive_indicators = [
            r'\b(thanks?|helpful|appreciate|great|awesome|perfect|excellent)\b',
            r'\b(exactly|spot on|this|that\'s right|correct|accurate)\b',
            r'\b(I agree|you\'re right|good point|well said)\b',
            r'\b(source|link|reference|documentation|guide)\b',
            r'\b(experience|tried|used|worked|tested|found)\b',
            r'\b(recommend|suggest|advise|consider|try)\b',
            r'\b(helpful|useful|valuable|informative|insightful)\b'
        ]
        
        self.negative_indicators = [
            r'\b(spam|advertisement|promotion|buy now|click here)\b',
            r'\b(guaranteed|100%|amazing deal|limited time|act now)\b',
            r'\b(make money|get rich|work from home|earn \$)\b',
            r'\b(free money|easy money|no effort|instant)\b',
            r'[A-Z]{4,}',  # Excessive caps (4+ consecutive)
            r'!{3,}',      # Multiple exclamation marks
            r'\?{3,}',     # Multiple question marks
            r'www\.|http[s]?://[^\s]+\.(com|net|org)/[^\s]*affiliate',  # Affiliate links
        ]
        
        # Enhanced Reddit tone indicators
        self.reddit_tone_positive = [
            r'\b(tbh|imo|imho|fwiw|til|afaik|iirc)\b',  # Reddit abbreviations
            r'\b(edit:|update:|tldr:|eli5:)\b',
            r'\b(source:|sources?:)\b',
            r'\b(this guy|this person|op|original poster)\b',
            r'\b(subreddit|sub|community)\b'
        ]
        
        # Spam and low-quality patterns
        self.spam_patterns = [
            r'\b(dm me|message me|contact me)\b',
            r'\b(check out my|visit my|follow me)\b',
            r'\b(upvote if|like if|share if)\b',
            r'\b(first|second|third)!\s*$',  # "First!" type comments
        ]
        
        # Quality enhancement patterns
        self.quality_patterns = [
            r'\b(here\'s how|step by step|follow these|try this)\b',
            r'\b(in my experience|from what I\'ve seen|personally)\b',
            r'\b(according to|based on|research shows)\b',
            r'\b(pros and cons|advantages|disadvantages)\b'
        ]

    def score_response(self, response: str, context: Optional[str] = None, post_title: str = "") -> Dict:
        """
        Enhanced response scoring with comprehensive quality analysis
        Returns detailed scoring breakdown with actionable feedback
        """
        if not response or len(response.strip()) < 10:
            return {
                'overall_score': 0,
                'breakdown': {
                    'relevance': 0,
                    'readability': 0,
                    'authenticity': 0,
                    'helpfulness': 0,
                    'compliance': 0
                },
                'feedback': ['Response too short or empty'],
                'grade': 'F',
                'quality_flags': ['TOO_SHORT'],
                'manual_review_required': True,
                'improvement_suggestions': ['Provide a more substantial response with at least 20 words']
            }
        
        scores = {}
        feedback = []
        quality_flags = []
        
        # 1. Relevance Score (0-100) - Weight: 25%
        relevance_score, relevance_feedback = self._score_relevance(response, post_title, context)
        scores['relevance'] = relevance_score
        feedback.extend(relevance_feedback)
        
        # 2. Readability Score (0-100) - Weight: 15%
        readability_score, readability_feedback = self._score_readability(response)
        scores['readability'] = readability_score
        feedback.extend(readability_feedback)
        
        # 3. Authenticity Score (0-100) - Weight: 20%
        authenticity_score, authenticity_feedback = self._score_authenticity(response)
        scores['authenticity'] = authenticity_score
        feedback.extend(authenticity_feedback)
        
        # 4. Helpfulness Score (0-100) - Weight: 25%
        helpfulness_score, helpfulness_feedback = self._score_helpfulness(response)
        scores['helpfulness'] = helpfulness_score
        feedback.extend(helpfulness_feedback)
        
        # 5. Compliance Score (0-100) - Weight: 15%
        compliance_score, compliance_feedback = self._score_compliance(response)
        scores['compliance'] = compliance_score
        feedback.extend(compliance_feedback)
        
        # Calculate weighted overall score
        weights = {
            'relevance': 0.25,
            'readability': 0.15,
            'authenticity': 0.20,
            'helpfulness': 0.25,
            'compliance': 0.15
        }
        
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        # Generate quality flags
        quality_flags = self._generate_quality_flags(scores, overall_score)
        
        # Determine if manual review is required
        manual_review_required = self._requires_manual_review(scores, overall_score, quality_flags)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(scores, quality_flags)
        
        # Get letter grade
        grade = self._get_grade(overall_score)
        
        return {
            'overall_score': round(overall_score, 1),
            'breakdown': scores,
            'feedback': feedback,
            'grade': grade,
            'quality_flags': quality_flags,
            'manual_review_required': manual_review_required,
            'improvement_suggestions': improvement_suggestions,
            'scoring_metadata': {
                'weights': weights,
                'thresholds_used': {
                    'auto_approve': self.thresholds.AUTO_APPROVE,
                    'manual_review': self.thresholds.MANUAL_REVIEW,
                    'reject': self.thresholds.REJECT
                },
                'scored_at': datetime.utcnow().isoformat()
            }
        }

    def _score_relevance(self, response: str, post_title: str, context: Optional[str] = None) -> tuple:
        """Score how relevant the response is to the original post"""
        score = 50  # Base score
        feedback = []
        
        if not post_title:
            return score, feedback
        
        # Extract key terms from post title
        post_words = set(re.findall(r'\b\w+\b', post_title.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        # Calculate word overlap
        common_words = post_words.intersection(response_words)
        if len(post_words) > 0:
            overlap_ratio = len(common_words) / len(post_words)
            score += overlap_ratio * 30
            
            if overlap_ratio > 0.3:
                feedback.append("Good keyword relevance to original post")
            elif overlap_ratio < 0.1:
                feedback.append("Low keyword relevance - consider addressing the main topic")
        
        # Check for direct addressing
        if any(word in response.lower() for word in ['you', 'your', 'op', 'original poster']):
            score += 10
            feedback.append("Directly addresses the poster")
        
        # Check for question answering
        if '?' in post_title and any(word in response.lower() for word in ['yes', 'no', 'try', 'use', 'check']):
            score += 10
            feedback.append("Attempts to answer the question")
        
        return min(100, max(0, score)), feedback

    def _score_readability(self, response: str) -> tuple:
        """Score readability and clarity"""
        score = 50
        feedback = []
        
        try:
            # Use textstat for readability metrics
            flesch_score = flesch_reading_ease(response)
            
            # Flesch Reading Ease: 60-70 is ideal for general audience
            if 60 <= flesch_score <= 80:
                score += 30
                feedback.append("Excellent readability level")
            elif 50 <= flesch_score < 60 or 80 < flesch_score <= 90:
                score += 20
                feedback.append("Good readability level")
            elif flesch_score < 30:
                score -= 20
                feedback.append("Text may be too complex - consider simplifying")
            elif flesch_score > 90:
                score -= 10
                feedback.append("Text may be too simple")
        except:
            pass  # Fallback if textstat fails
        
        # Length check
        word_count = len(response.split())
        if 20 <= word_count <= 150:
            score += 15
            feedback.append("Good response length")
        elif word_count < 10:
            score -= 20
            feedback.append("Response too short")
        elif word_count > 300:
            score -= 10
            feedback.append("Response may be too long for Reddit")
        
        # Sentence structure
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        if 10 <= avg_sentence_length <= 20:
            score += 5
            feedback.append("Good sentence length")
        
        return min(100, max(0, score)), feedback

    def _score_authenticity(self, response: str) -> tuple:
        """Score how authentic and human-like the response sounds"""
        score = 50
        feedback = []
        
        response_lower = response.lower()
        
        # Check for positive authenticity indicators
        positive_matches = sum(1 for pattern in self.positive_indicators 
                             if re.search(pattern, response_lower, re.IGNORECASE))
        score += min(positive_matches * 8, 25)
        
        # Check for Reddit-specific tone
        reddit_matches = sum(1 for pattern in self.reddit_tone_positive 
                           if re.search(pattern, response_lower, re.IGNORECASE))
        score += min(reddit_matches * 5, 15)
        
        if reddit_matches > 0:
            feedback.append("Uses appropriate Reddit tone")
        
        # Check for negative indicators (spam-like content)
        negative_matches = sum(1 for pattern in self.negative_indicators 
                             if re.search(pattern, response_lower, re.IGNORECASE))
        score -= negative_matches * 15
        
        if negative_matches > 0:
            feedback.append("Contains promotional or spam-like language")
        
        # Check for personal experience indicators
        experience_indicators = ['i', 'my', 'me', 'personally', 'in my experience']
        if any(indicator in response_lower for indicator in experience_indicators):
            score += 10
            feedback.append("Includes personal perspective")
        
        # Avoid overly formal language
        formal_indicators = ['furthermore', 'moreover', 'consequently', 'therefore', 'thus']
        formal_count = sum(1 for indicator in formal_indicators if indicator in response_lower)
        if formal_count > 2:
            score -= 10
            feedback.append("May sound too formal for Reddit")
        
        return min(100, max(0, score)), feedback

    def _score_helpfulness(self, response: str) -> tuple:
        """Enhanced helpfulness scoring with comprehensive analysis"""
        score = 50
        feedback = []
        
        response_lower = response.lower()
        
        # High-value helpful elements (higher scores)
        high_value_elements = [
            ('specific steps/instructions', r'(\d+\.|step \d+|first[,:]|second[,:]|third[,:]|next[,:]|then[,:]|finally[,:])', 12),
            ('concrete recommendations', r'\b(try|use|check|consider|recommend|suggest|go with|opt for)\b', 10),
            ('detailed explanations', r'\b(because|since|due to|reason|why|how|this is because|the reason is)\b', 8),
            ('multiple alternatives', r'\b(alternatively|instead|or you could|another option|you might also|consider also)\b', 10),
            ('troubleshooting help', r'\b(if that doesn\'t work|if not|otherwise|as a backup|plan b)\b', 12)
        ]
        
        for element_name, pattern, points in high_value_elements:
            matches = len(re.findall(pattern, response_lower))
            if matches > 0:
                score += min(matches * points, points * 2)  # Cap at 2x base points
                feedback.append(f"Includes {element_name} ({matches} instances)")
        
        # Medium-value helpful elements
        medium_value_elements = [
            ('external resources', r'(http[s]?://|www\.|\.com|\.org|\.edu|subreddit|r/)', 8),
            ('personal experience', r'\b(i\'ve|i have|in my experience|personally|from experience|i found)\b', 6),
            ('specific examples', r'\b(for example|such as|like|including|e\.g\.|i\.e\.)\b', 6),
            ('time estimates', r'\b(\d+\s*(minutes?|hours?|days?|weeks?)|takes about|usually takes)\b', 5),
            ('cost information', r'\b(\$\d+|costs?|price|expensive|cheap|free|budget)\b', 5)
        ]
        
        for element_name, pattern, points in medium_value_elements:
            if re.search(pattern, response_lower):
                score += points
                feedback.append(f"Includes {element_name}")
        
        # Quality enhancement patterns
        quality_patterns = [
            ('structured approach', r'\b(here\'s how|step by step|follow these|here\'s what)\b', 8),
            ('pros and cons', r'\b(pros and cons|advantages|disadvantages|benefits|drawbacks)\b', 10),
            ('warnings/cautions', r'\b(be careful|watch out|warning|caution|note that|keep in mind)\b', 6),
            ('follow-up support', r'\b(let me know|feel free|if you need|happy to help|any questions)\b', 5)
        ]
        
        for pattern_name, pattern, points in quality_patterns:
            if re.search(pattern, response_lower):
                score += points
                feedback.append(f"Shows {pattern_name}")
        
        # Actionable advice scoring
        action_words = [
            'try', 'use', 'check', 'visit', 'download', 'install', 'contact', 
            'search', 'look', 'find', 'ask', 'call', 'email', 'apply', 'start'
        ]
        action_count = sum(1 for word in action_words if f' {word} ' in f' {response_lower} ')
        if action_count > 0:
            action_score = min(action_count * 3, 15)
            score += action_score
            feedback.append(f"Provides actionable advice ({action_count} action words)")
        
        # Depth and detail scoring
        word_count = len(response.split())
        if 50 <= word_count <= 200:  # Sweet spot for helpful responses
            score += 10
            feedback.append("Good detail level")
        elif 200 < word_count <= 300:
            score += 5
            feedback.append("Comprehensive detail")
        elif word_count < 20:
            score -= 10
            feedback.append("Too brief to be helpful")
        
        # Penalize unhelpful patterns
        unhelpful_patterns = [
            ('vague responses', ['it depends', 'maybe', 'possibly', 'might work', 'not sure', 'hard to say'], -8),
            ('dismissive language', ['just google it', 'figure it out', 'obvious', 'duh', 'everyone knows'], -15),
            ('non-answers', ['i don\'t know', 'no idea', 'can\'t help', 'not my problem'], -12),
            ('circular reasoning', ['because it is', 'that\'s just how', 'it works that way'], -6)
        ]
        
        for pattern_name, phrases, penalty in unhelpful_patterns:
            matches = sum(1 for phrase in phrases if phrase in response_lower)
            if matches > 0:
                score += penalty * matches  # Penalty is negative
                feedback.append(f"Contains {pattern_name} ({matches} instances)")
        
        # Bonus for comprehensive responses
        if score >= 80:
            comprehensive_indicators = [
                'multiple solutions', 'different approaches', 'various options',
                'depends on', 'context matters', 'several ways'
            ]
            if any(indicator in response_lower for indicator in comprehensive_indicators):
                score += 5
                feedback.append("Acknowledges complexity and provides comprehensive help")
        
        # Final helpfulness assessment
        if score >= 85:
            feedback.append("Exceptionally helpful response")
        elif score >= 70:
            feedback.append("Very helpful response")
        elif score < 50:
            feedback.append("Limited helpfulness - consider adding more specific advice")
        
        return min(100, max(0, score)), feedback

    def _score_compliance(self, response: str) -> tuple:
        """Enhanced compliance scoring with Reddit rules and best practices"""
        score = 85  # Start high, deduct for violations
        feedback = []
        
        response_lower = response.lower()
        
        # Major rule violations (heavy penalties)
        major_violations = [
            ('self-promotion', r'\b(my (website|blog|channel|product|business)|check out my|visit my)\b'),
            ('spam indicators', r'\b(buy now|click here|limited time|act now|special offer)\b'),
            ('personal info', r'\b(\d{3}-\d{3}-\d{4}|\w+@\w+\.\w+|call me|text me)\b'),
            ('harassment', r'\b(idiot|stupid|moron|shut up|loser|pathetic)\b'),
            ('vote manipulation', r'\b(upvote (this|me)|downvote|give me karma)\b'),
            ('affiliate links', r'(amazon\.com/.*[?&]tag=|bit\.ly|tinyurl|affiliate)')
        ]
        
        for violation_type, pattern in major_violations:
            if re.search(pattern, response_lower, re.IGNORECASE):
                score -= 25
                feedback.append(f"Major violation: {violation_type} detected")
        
        # Minor violations (moderate penalties)
        minor_violations = [
            ('excessive caps', r'[A-Z]{4,}'),
            ('excessive punctuation', r'[!]{3,}|[?]{3,}'),
            ('repetitive text', r'(.{10,})\1{2,}'),  # Same text repeated 3+ times
            ('all caps words', r'\b[A-Z]{3,}\b')
        ]
        
        for violation_type, pattern in minor_violations:
            matches = len(re.findall(pattern, response))
            if matches > 0:
                penalty = min(matches * 5, 15)  # Max 15 points penalty
                score -= penalty
                feedback.append(f"Minor violation: {violation_type} ({matches} instances)")
        
        # Check for spam patterns
        spam_matches = sum(1 for pattern in self.spam_patterns 
                          if re.search(pattern, response_lower, re.IGNORECASE))
        if spam_matches > 0:
            score -= spam_matches * 10
            feedback.append(f"Spam-like patterns detected ({spam_matches} instances)")
        
        # Positive compliance indicators
        positive_indicators = [
            ('respectful language', ['please', 'thank you', 'thanks', 'appreciate']),
            ('helpful phrases', ['hope this helps', 'good luck', 'let me know', 'feel free']),
            ('community spirit', ['welcome to reddit', 'great community', 'fellow redditor']),
            ('source attribution', ['source:', 'according to', 'based on', 'reference:'])
        ]
        
        for indicator_type, phrases in positive_indicators:
            if any(phrase in response_lower for phrase in phrases):
                score += 3
                feedback.append(f"Positive indicator: {indicator_type}")
        
        # Length and structure checks
        word_count = len(response.split())
        if 20 <= word_count <= 300:  # Appropriate length
            score += 5
            feedback.append("Appropriate response length")
        elif word_count > 500:
            score -= 5
            feedback.append("Response may be too long for Reddit")
        elif word_count < 10:
            score -= 10
            feedback.append("Response too short to be helpful")
        
        # Check for balanced tone (not overly excited or negative)
        exclamation_count = response.count('!')
        if exclamation_count <= 2:
            score += 3
        elif exclamation_count > 5:
            score -= 5
            feedback.append("Overly excited tone")
        
        # Reddit etiquette checks
        if re.search(r'\b(edit:|update:)\b', response_lower):
            score += 5
            feedback.append("Follows Reddit edit etiquette")
        
        if re.search(r'\b(tldr:|tl;dr:)\b', response_lower):
            score += 3
            feedback.append("Includes helpful summary")
        
        # Final compliance assessment
        if score >= 90:
            feedback.append("Excellent compliance with Reddit guidelines")
        elif score >= 80:
            feedback.append("Good compliance with minor areas for improvement")
        elif score < 60:
            feedback.append("Significant compliance issues require attention")
        
        return min(100, max(0, score)), feedback

    def _get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade with enhanced grading scale"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "C-"
        elif score >= 50:
            return "D"
        else:
            return "F"
    
    def _generate_quality_flags(self, scores: Dict, overall_score: float) -> List[str]:
        """Generate quality flags based on scoring results"""
        flags = []
        
        # Overall quality flags
        if overall_score >= self.thresholds.EXCELLENT:
            flags.append("EXCELLENT_QUALITY")
        elif overall_score >= self.thresholds.AUTO_APPROVE:
            flags.append("AUTO_APPROVE_CANDIDATE")
        elif overall_score <= self.thresholds.REJECT:
            flags.append("REJECT_CANDIDATE")
        
        # Dimension-specific flags
        if scores['relevance'] < self.thresholds.RELEVANCE_MIN:
            flags.append("LOW_RELEVANCE")
        
        if scores['readability'] < self.thresholds.READABILITY_MIN:
            flags.append("POOR_READABILITY")
        
        if scores['authenticity'] < self.thresholds.AUTHENTICITY_MIN:
            flags.append("INAUTHENTIC_TONE")
        
        if scores['helpfulness'] < self.thresholds.HELPFULNESS_MIN:
            flags.append("LOW_HELPFULNESS")
        
        if scores['compliance'] < self.thresholds.COMPLIANCE_MIN:
            flags.append("COMPLIANCE_RISK")
        
        # Special quality indicators
        if all(score >= 85 for score in scores.values()):
            flags.append("ALL_DIMENSIONS_EXCELLENT")
        
        if any(score <= 40 for score in scores.values()):
            flags.append("CRITICAL_DIMENSION_FAILURE")
        
        return flags
    
    def _requires_manual_review(self, scores: Dict, overall_score: float, quality_flags: List[str]) -> bool:
        """Determine if response requires manual review"""
        
        # Auto-reject conditions
        if overall_score <= self.thresholds.REJECT:
            return True
        
        # Critical flags that require review
        critical_flags = [
            "COMPLIANCE_RISK", 
            "CRITICAL_DIMENSION_FAILURE",
            "REJECT_CANDIDATE"
        ]
        
        if any(flag in quality_flags for flag in critical_flags):
            return True
        
        # Compliance threshold is strict
        if scores['compliance'] < self.thresholds.COMPLIANCE_MIN:
            return True
        
        # Multiple low scores require review
        low_scores = sum(1 for score in scores.values() if score < 60)
        if low_scores >= 2:
            return True
        
        # Overall score in manual review range
        if self.thresholds.MANUAL_REVIEW <= overall_score < self.thresholds.AUTO_APPROVE:
            return True
        
        return False
    
    def _generate_improvement_suggestions(self, scores: Dict, quality_flags: List[str]) -> List[str]:
        """Generate detailed, actionable improvement suggestions"""
        suggestions = []
        
        # Relevance improvements
        if scores['relevance'] < self.thresholds.RELEVANCE_MIN:
            suggestions.extend([
                "Include more keywords from the original post title",
                "Directly address the poster's question or concern",
                "Reference specific details mentioned in the original post"
            ])
        
        # Readability improvements
        if scores['readability'] < self.thresholds.READABILITY_MIN:
            suggestions.extend([
                "Use shorter, simpler sentences (aim for 15-20 words per sentence)",
                "Break up long paragraphs into smaller chunks",
                "Use common words instead of complex vocabulary",
                "Add bullet points or numbered lists for clarity"
            ])
        
        # Authenticity improvements
        if scores['authenticity'] < self.thresholds.AUTHENTICITY_MIN:
            suggestions.extend([
                "Add personal experience or anecdotes",
                "Use more conversational language and contractions",
                "Include Reddit-appropriate abbreviations (IMO, TBH, etc.)",
                "Avoid overly formal or corporate language"
            ])
        
        # Helpfulness improvements
        if scores['helpfulness'] < self.thresholds.HELPFULNESS_MIN:
            suggestions.extend([
                "Provide specific, actionable steps or recommendations",
                "Include relevant links or resources",
                "Offer alternative solutions or approaches",
                "Explain the reasoning behind your suggestions"
            ])
        
        # Compliance improvements
        if scores['compliance'] < self.thresholds.COMPLIANCE_MIN:
            suggestions.extend([
                "Remove any promotional or sales language",
                "Avoid excessive capitalization or punctuation",
                "Ensure content follows Reddit community guidelines",
                "Remove any personal contact information or links"
            ])
        
        # Flag-specific suggestions
        if "LOW_RELEVANCE" in quality_flags:
            suggestions.append("Focus more directly on the original poster's specific question")
        
        if "POOR_READABILITY" in quality_flags:
            suggestions.append("Simplify language and sentence structure for better comprehension")
        
        if "INAUTHENTIC_TONE" in quality_flags:
            suggestions.append("Adopt a more natural, conversational Reddit tone")
        
        if "COMPLIANCE_RISK" in quality_flags:
            suggestions.append("Review content for potential policy violations")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:8]  # Limit to top 8 suggestions
    
    def get_quality_summary(self, scoring_result: Dict) -> Dict:
        """Generate a comprehensive quality summary"""
        scores = scoring_result['breakdown']
        overall_score = scoring_result['overall_score']
        grade = scoring_result['grade']
        
        # Determine quality level
        if overall_score >= self.thresholds.EXCELLENT:
            quality_level = "Excellent"
            quality_description = "Outstanding response that exceeds expectations"
        elif overall_score >= self.thresholds.GOOD:
            quality_level = "Good"
            quality_description = "High-quality response ready for use"
        elif overall_score >= self.thresholds.ACCEPTABLE:
            quality_level = "Acceptable"
            quality_description = "Adequate response with minor improvements needed"
        elif overall_score >= self.thresholds.NEEDS_IMPROVEMENT:
            quality_level = "Needs Improvement"
            quality_description = "Response requires significant improvements"
        else:
            quality_level = "Poor"
            quality_description = "Response needs major revision or replacement"
        
        # Find strongest and weakest dimensions
        strongest_dimension = max(scores.keys(), key=lambda k: scores[k])
        weakest_dimension = min(scores.keys(), key=lambda k: scores[k])
        
        return {
            "quality_level": quality_level,
            "quality_description": quality_description,
            "grade": grade,
            "overall_score": overall_score,
            "strongest_dimension": {
                "name": strongest_dimension,
                "score": scores[strongest_dimension]
            },
            "weakest_dimension": {
                "name": weakest_dimension,
                "score": scores[weakest_dimension]
            },
            "dimensions_above_threshold": sum(1 for score in scores.values() if score >= 70),
            "total_dimensions": len(scores),
            "ready_for_use": not scoring_result.get('manual_review_required', True)
        }

    def get_improvement_suggestions(self, scores: Dict) -> List[str]:
        """Legacy method for backward compatibility"""
        quality_flags = self._generate_quality_flags(scores, sum(scores.values()) / len(scores))
        return self._generate_improvement_suggestions(scores, quality_flags)