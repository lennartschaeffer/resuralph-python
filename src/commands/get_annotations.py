import os
import logging
import requests
from urllib.parse import quote

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
            return "An error occurred while processing your request. 😔"
        
        # Extract pdf_url from command options
        options = interaction_data.get('data', {}).get('options', [])
        pdf_url = None
        for option in options:
            if option.get('name') == 'pdf_url':
                pdf_url = option.get('value')
                break
        
        if not pdf_url:
            logger.error(f"No pdf_url provided for user {user_id}")
            return "Please provide a PDF URL to get annotations."
        
        logger.info(f"Getting annotations for user {user_id} with URL: {pdf_url}")
        
        # Get annotations from Hypothesis
        annotations = get_annotations_from_hypothesis(pdf_url)
        if not annotations:
            return "An error occurred on Hypothes.is's end. Please try again later or visit the link instead to see annotations 😔"
        
        # Format and return annotations
        return format_annotations(annotations, user_id)
        
    except Exception as e:
        logger.error(f"Error in get_annotations command: {str(e)}")
        return "An error occurred while getting annotations. 😔"


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
    Format annotations into Discord message content
    
    Args:
        annotations (dict): Annotations data from Hypothesis
        user_id (str): Discord user ID for logging
        
    Returns:
        str: Formatted message for Discord
    """
    try:
        # Check if there are no annotations
        if annotations.get('total', 0) == 0:
            return "📝 **No Annotations Yet!**\nNo annotations were currently found for this resume."
        
        # Build the response message
        message_parts = ["📝 **Resume Feedback**\nHere are the annotations for your resume:\n"]
        
        annotations_list = annotations.get('rows', [])
        fields_added = 0
        max_fields = 25  # Discord embed limit
        
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
            
            field_content = f"📄 *{resume_text}*\n💭 {annotation_text}\n👤 by {user_name}\n──────────────\n"
            message_parts.append(field_content)
            fields_added += 1
        
        # Handle additional annotations if there are more than 25
        if annotations.get('total', 0) > max_fields:
            remaining_count = annotations.get('total', 0) - max_fields
            if remaining_count > 25:
                message_parts.append(f"\n⚠️ **Note:** There are {remaining_count} more annotations! Please check the Hypothesis link for complete details.")
            else:
                # Add remaining annotations
                remaining_annotations = annotations_list[fields_added:]
                message_parts.append("\n📝 **Feedback Cont'd**\nAdditional annotations for your resume:\n")
                
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
                    
                    field_content = f"📄 *{resume_text}*\n💭 {annotation_text}\n👤 by {user_name}\n──────────────\n"
                    message_parts.append(field_content)
        
        message_parts.append("\n🤖 ResuRalph by @Lenny")
        
        final_message = "".join(message_parts)
        
        # Discord has a 2000 character limit for messages
        if len(final_message) > 2000:
            final_message = final_message[:1900] + "...\n\n⚠️ Message truncated due to length. Check the Hypothesis link for complete annotations."
        
        logger.info(f"Formatted {fields_added} annotations for user {user_id}")
        return final_message
        
    except Exception as e:
        logger.error(f"Error formatting annotations: {str(e)}")
        return "An error occurred while formatting annotations. 😔"