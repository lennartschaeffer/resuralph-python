import os
import logging
import requests
from urllib.parse import quote
from helpers.embed_helper import create_error_embed, create_info_embed

logger = logging.getLogger(__name__)


def handle_get_annotations_command(interaction_data):
    """
    Handle the /get_annotations command
    
    Args:
        interaction_data (dict): Discord interaction data
        
    Returns:
        str: Response message for Discord
    """
    try:
        user_id = interaction_data.get('member', {}).get('user', {}).get('id')
        if not user_id:
            logger.error("Could not extract user ID from interaction data")
            return create_error_embed(
                "Processing Error",
                "An error occurred while processing your request. 😔"
            )
        
        # Extract pdf_url from command options
        options = interaction_data.get('data', {}).get('options', [])
        pdf_url = None
        for option in options:
            if option.get('name') == 'pdf_url':
                pdf_url = option.get('value')
                break
        
        if not pdf_url:
            logger.error(f"No pdf_url provided for user {user_id}")
            return create_error_embed(
                "Missing PDF URL",
                "Please provide a PDF URL to get annotations."
            )
        
        logger.info(f"Getting annotations for user {user_id} with URL: {pdf_url}")
        
        # Get annotations from Hypothesis
        annotations = get_annotations_from_hypothesis(pdf_url)
        if not annotations:
            return create_error_embed(
                "Hypothesis API Error",
                "An error occurred on Hypothes.is's end. Please try again later or visit the link instead to see annotations 😔"
            )
        
        # Format and return annotations
        return format_annotations(annotations, user_id)
        
    except Exception as e:
        logger.error(f"Error in get_annotations command: {str(e)}")
        return create_error_embed(
            "Annotation Error",
            "An error occurred while getting annotations. 😔"
        )


def get_annotations_from_hypothesis(pdf_url):
    """
    Fetch annotations from Hypothesis API
    
    Args:
        pdf_url (str): URL of the PDF to get annotations for
        
    Returns:
        dict or None: Annotations data from Hypothesis API
    """
    try:
        api_url = f"https://api.hypothes.is/api/search?uri={quote(pdf_url)}&limit=100&order=asc"
        
        headers = {
            'Authorization': f'Bearer {os.getenv("HYPOTHESIS_API_KEY")}'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        annotations_data = response.json()
        logger.info(f"Retrieved {annotations_data.get('total', 0)} annotations from Hypothesis")
        
        return annotations_data
        
    except Exception as e:
        logger.error(f"Error fetching annotations from Hypothesis: {str(e)}")
        return None


def format_annotations(annotations, user_id):
    """
    Format annotations into Discord embed format
    
    Args:
        annotations (dict): Annotations data from Hypothesis
        user_id (str): Discord user ID for logging
        
    Returns:
        dict: Discord response data with embeds
    """
    try:
        # Check if there are no annotations
        if annotations.get('total', 0) == 0:
            embed = {
                "color": 0xffff00,  # Yellow color
                "title": "📝 No Annotations Yet!",
                "description": "No annotations were currently found for this resume.",
                "footer": {
                    "text": "🤖 ResuRalph by @Lenny"
                }
            }
            return {"embeds": [embed]}
        
        # Create primary embed
        embed = {
            "color": 0x0099ff,  # Blue color
            "title": "📝 Resume Feedback",
            "description": "Here are the annotations for your resume:",
            "footer": {
                "text": "🤖 ResuRalph by @Lenny"
            },
            "fields": []
        }
        
        annotations_list = annotations.get('rows', [])
        fields_added = 0
        max_fields = 25  # Discord embed limit
        
        # Add fields to primary embed
        for annotation in annotations_list:
            if fields_added >= max_fields:
                break
            
            # Extract resume text from target selector
            resume_text = ""
            targets = annotation.get('target', [])
            for target in targets:
                selectors = target.get('selector', [])
                if len(selectors) > 1 and selectors[1].get('exact'):
                    resume_text = selectors[1]['exact']
                    if len(resume_text) >= 240:
                        resume_text = resume_text[:240] + "..."
                    break
            
            # Format annotation
            annotation_text = annotation.get('text', '')
            user_name = annotation.get('user', '').replace('acct:', '').replace('@hypothes.is', '')
            
            field = {
                "name": f"📄 *{resume_text}*",
                "value": f"💭 {annotation_text}\n👤 by {user_name}\n──────────────",
                "inline": False
            }
            
            embed["fields"].append(field)
            fields_added += 1
        
        embeds = [embed]
        
        # Handle additional annotations if there are more than 25
        if annotations.get('total', 0) > max_fields:
            remaining_count = annotations.get('total', 0) - max_fields
            remaining_annotations = annotations_list[fields_added:]
            
            if remaining_count > 25:
                # Too many annotations, show warning
                warning_embed = {
                    "color": 0xff9900,  # Orange color for warning
                    "title": "⚠️ Additional Annotations",
                    "description": f"There are {remaining_count} more annotations! Please check the Hypothesis link for complete details.",
                    "footer": {
                        "text": "🤖 ResuRalph by @Lenny"
                    }
                }
                embeds.append(warning_embed)
            else:
                # Create secondary embed for remaining annotations
                secondary_embed = {
                    "color": 0x0099ff,  # Blue color
                    "title": "📝 Feedback Cont'd",
                    "description": "Additional annotations for your resume:",
                    "footer": {
                        "text": "🤖 ResuRalph by @Lenny"
                    },
                    "fields": []
                }
                
                for annotation in remaining_annotations:
                    # Extract resume text
                    resume_text = ""
                    targets = annotation.get('target', [])
                    for target in targets:
                        selectors = target.get('selector', [])
                        if len(selectors) > 1 and selectors[1].get('exact'):
                            resume_text = selectors[1]['exact']
                            if len(resume_text) >= 240:
                                resume_text = resume_text[:240] + "..."
                            break
                    
                    # Format annotation
                    annotation_text = annotation.get('text', '')
                    user_name = annotation.get('user', '').replace('acct:', '').replace('@hypothes.is', '')
                    
                    field = {
                        "name": f"📄 *{resume_text}*",
                        "value": f"💭 {annotation_text}\n👤 by {user_name}\n──────────────",
                        "inline": False
                    }
                    
                    secondary_embed["fields"].append(field)
                
                embeds.append(secondary_embed)
        
        logger.info(f"Formatted {fields_added} annotations into {len(embeds)} embed(s) for user {user_id}")
        return {"embeds": embeds}
        
    except Exception as e:
        logger.error(f"Error formatting annotations: {str(e)}")
        return create_error_embed(
            "Formatting Error",
            "An error occurred while formatting annotations. 😔"
        )