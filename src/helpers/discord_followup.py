import requests
import logging
import threading
import os

logger = logging.getLogger(__name__)


def send_followup_message(application_id, interaction_token, content):
    """
    Send a follow-up message to Discord using the interaction token
    
    Args:
        application_id (str): Discord application ID
        interaction_token (str): Token from the original interaction
        content (str): Message content to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
        
        payload = {
            "content": content
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Follow-up message sent successfully: {len(content)} characters")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send follow-up message: {str(e)}")
        return False


def process_update_command_async(interaction_data, application_id, interaction_token):
    """
    Process the update command asynchronously and send follow-up message
    
    Args:
        interaction_data (dict): Original Discord interaction data
        application_id (str): Discord application ID  
        interaction_token (str): Token for follow-up messages
    """
    try:
        # Import here to avoid circular imports
        from commands.update import handle_update_command
        
        logger.info("Starting async update command processing")
        
        # Process the command
        result_message = handle_update_command(interaction_data)
        
        # Send the result as a follow-up message
        success = send_followup_message(application_id, interaction_token, result_message)
        
        if not success:
            # Try to send an error message if the main response failed
            error_msg = "An error occurred while processing your update. Please try again."
            send_followup_message(application_id, interaction_token, error_msg)
        
        logger.info("Async update command processing completed")
        
    except Exception as e:
        logger.error(f"Error in async update processing: {str(e)}")
        error_msg = "An error occurred while updating your resume. 😔"
        send_followup_message(application_id, interaction_token, error_msg)


def start_async_update_command(interaction_data):
    """
    Start async processing of update command and return immediate deferred response
    
    Args:
        interaction_data (dict): Discord interaction data
        
    Returns:
        dict: Discord deferred response
    """
    try:
        # Extract the application ID and interaction token
        application_id = interaction_data.get('application_id')
        interaction_token = interaction_data.get('token')
        
        if not application_id or not interaction_token:
            logger.error("Missing application_id or token for deferred response")
            return {
                "type": 4,
                "data": {"content": "An error occurred while processing your request."}
            }
        
        # Start async processing in a separate thread
        thread = threading.Thread(
            target=process_update_command_async,
            args=(interaction_data, application_id, interaction_token)
        )
        thread.daemon = True
        thread.start()
        
        logger.info("Started async thread for update command processing")
        
        # Return deferred response immediately
        return {
            "type": 5  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
        }
        
    except Exception as e:
        logger.error(f"Error starting async update command: {str(e)}")
        return {
            "type": 4,
            "data": {"content": "An error occurred while processing your request."}
        }