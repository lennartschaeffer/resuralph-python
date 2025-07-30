import os
import logging
from openai import OpenAI
from typing import List, Dict, Optional
import json
import dotenv

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    def __init__(self):
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def analyze_resume(self, resume_text: str) -> Optional[List[Dict]]:
        
        try:
            prompt = self._create_analysis_prompt(resume_text)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert resume reviewer and career coach. Provide specific, actionable feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            feedback_json = response.choices[0].message.content
            
            if not feedback_json:
                logger.error("AI response is empty or invalid")
                return None
            
            feedback_data = json.loads(feedback_json)
            
            logger.info(f"Generated {len(feedback_data.get('feedback', []))} feedback items")
            
            return feedback_data.get('feedback', [])
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error analyzing resume with AI: {str(e)}")
            return None
    
    def _create_analysis_prompt(self, resume_text: str) -> str:
        """Create structured prompt for resume analysis"""
        return f"""
Analyze this resume and provide specific, actionable feedback. For each piece of feedback, identify the exact text from the resume that you're commenting on.

Resume Content:
{resume_text}

Please respond with a JSON object in this exact format:
{{
    "feedback": [
        {{
            "selected_text": "exact text from resume being reviewed",
            "feedback_type": "improvement|formatting",
            "comment": "specific actionable feedback (keep under 200 characters)",
            "priority": "high|medium|low"
        }}
    ]
}}

Focus on:
1. **Experience Section and Projects Section**: These are typically the most needed areas for improvement
2. **Content Quality**: Action statements, experience/project descriptions, quantified achievements, impacts
3. **ATS Optimization**: Keywords, formatting, structure
4. **Professional Presentation**: Grammar, consistency, clarity

Guidelines:
- Select specific text snippets (10-50 words) that you're commenting on
- Provide actionable, constructive feedback, and be critical
- Only focus on improvement areas, not general praise
- Use clear, concise language
- Limit to 8-12 feedback items total
"""

    def format_feedback_for_hypothesis(self, feedback_items: List[Dict], resume_url: str) -> List[Dict]:
        annotations = []
        
        for item in feedback_items:
            # Map feedback type to emoji and color
            type_mapping = {
                'improvement': {'emoji': '🔧', 'tag': 'improvement'}, 
                'formatting': {'emoji': '📝', 'tag': 'formatting'}
            }
            
            feedback_type = item.get('feedback_type', 'improvement')
            mapping = type_mapping.get(feedback_type, type_mapping['improvement'])

            annotation = {
                'uri': resume_url,
                'target': [{
                    'source': resume_url,
                    'selector': [{
                        'type': 'TextQuoteSelector',
                        'exact': item.get('selected_text', '')
                    }]
                }],
                'text': f"{mapping['emoji']} {item.get('comment', '')}",
                'tags': ['ai-review', mapping['tag'], f"priority-{item.get('priority', 'medium')}"],
                'group': '__world__',
                'permissions': {
                    'read': ['group:__world__'],
                    'admin': ['acct:lennartschaeffer@hypothes.is'],
                    'update': ['acct:lennartschaeffer@hypothes.is'],
                    'delete': ['acct:lennartschaeffer@hypothes.is']
                }
            }
            
            annotations.append(annotation)
            
        logger.info(f"Formatted {len(annotations)} annotations for Hypothesis")
        return annotations


# Global instance
resume_analyzer = ResumeAnalyzer()


def analyze_resume_text(resume_text: str) -> Optional[List[Dict]]:
    """Convenience function for analyzing resume text"""
    return resume_analyzer.analyze_resume(resume_text)


def format_feedback_for_annotations(feedback_items: List[Dict], resume_url: str) -> List[Dict]:
    """Convenience function for formatting feedback as annotations"""
    return resume_analyzer.format_feedback_for_hypothesis(feedback_items, resume_url)