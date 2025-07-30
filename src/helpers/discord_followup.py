import requests
import logging
import threading

logger = logging.getLogger(__name__)


def send_followup_message(application_id, interaction_token, content):
    """
    Send a follow-up message to Discord using the interaction token
    
    Args:
        application_id (str): Discord application ID
        interaction_token (str): Token from the original interaction
        content (str or dict): Message content to send (string for plain text, dict for embeds)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = f"https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}"
        
        # Check if content is an embed response or plain text
        if isinstance(content, dict) and "embeds" in content:
            payload = content  # Use the embed structure directly
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


def process_command_async(interaction_data, application_id, interaction_token, command_type):
    """
    Process a command asynchronously and send follow-up message
    
    Args:
        interaction_data (dict): Original Discord interaction data
        application_id (str): Discord application ID  
        interaction_token (str): Token for follow-up messages
        command_type (str): Type of command to process ('update' or 'ai_review')
    """
    try:
        logger.info(f"Starting async {command_type} command processing")
        
        # Import handlers dynamically to avoid circular imports
        if command_type == 'update':
            from commands.update import handle_update_command
            result_message = handle_update_command(interaction_data)
            error_context = "updating your resume"
        elif command_type == 'ai_review':
            from commands.ai_review import handle_ai_review_command
            result_message = handle_ai_review_command(interaction_data)
            error_context = "analyzing your resume"
        else:
            raise ValueError(f"Unknown command type: {command_type}")
        
        # Send the result as a follow-up message
        success = send_followup_message(application_id, interaction_token, result_message)
        
        if not success:
            # Try to send an error message if the main response failed
            error_msg = f"An error occurred while processing your {command_type}. Please try again."
            send_followup_message(application_id, interaction_token, error_msg)
        
        logger.info(f"Async {command_type} command processing completed")
        
    except Exception as e:
        logger.error(f"Error in async {command_type} processing: {str(e)}")
        error_msg = f"An error occurred while {error_context}. 😔"
        send_followup_message(application_id, interaction_token, error_msg)


def start_async_command(interaction_data, command_type):
    """
    Start async processing of a command and return immediate deferred response
    
    Args:
        interaction_data (dict): Discord interaction data
        command_type (str): Type of command to process ('update' or 'ai_review')
        
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
            target=process_command_async,
            args=(interaction_data, application_id, interaction_token, command_type)
        )
        thread.daemon = True # Make sure thread exits when main program does
        thread.start() 
        
        logger.info(f"Started async thread for {command_type} command processing")
        
        # Return deferred response immediately
        return {
            "type": 5  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
        }
        
    except Exception as e:
        logger.error(f"Error starting async {command_type} command: {str(e)}")
        return {
            "type": 4,
            "data": {"content": "An error occurred while processing your request."}
        }


