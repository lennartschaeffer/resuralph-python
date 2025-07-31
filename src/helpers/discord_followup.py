import requests
import logging

logger = logging.getLogger(__name__)


def send_followup_message(application_id, interaction_token, content):
    
    try:
        url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
        
        if isinstance(content, dict) and "embeds" in content:
            payload = content 
            log_message = f"Follow-up embed sent successfully: {len(content['embeds'])} embed(s)"
        else:
            payload = {
                "content": content
            }
            log_message = f"Follow-up message sent successfully: {len(content)} characters"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        logger.info(log_message)
        return True
        
    except Exception as e:
        logger.error(f"Failed to send follow-up message: {str(e)}")
        return False
