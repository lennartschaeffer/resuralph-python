import threading
import logging
from helpers.embed_helper import create_error_embed
from helpers.sqs_publisher import create_deferred_response

logger = logging.getLogger(__name__)


def process_async_command_thread(interaction_data, command_type, application_id, interaction_token):
    """
    Background thread function to process async commands locally.
    Replicates the logic from command_processor.py but runs in a thread.
    """
    try:
        logger.info(f"Processing {command_type} command in background thread")
        
        # Process the command using the same logic as the Lambda processor
        if command_type == 'update':
            from commands.update import handle_update_command
            result_message = handle_update_command(interaction_data)
        elif command_type == 'ai_review':
            from commands.ai_review import handle_ai_review_command
            result_message = handle_ai_review_command(interaction_data)
        else:
            logger.error(f"Unknown command type: {command_type}")
            result_message = f"Unknown command type: {command_type}"
        
        # Send follow-up message to Discord using the same helper as Lambda
        from helpers.discord_followup import send_followup_message
        success = send_followup_message(application_id, interaction_token, result_message)
        
        if not success:
            # Try to send error message if main result failed
            error_msg = f"An error occurred while processing your {command_type}. Please try again."
            send_followup_message(application_id, interaction_token, error_msg)
            
        logger.info(f"Successfully completed {command_type} command in background thread")
        
    except Exception as e:
        logger.error(f"Error in background thread processing {command_type}: {str(e)}")
        # Try to send error message
        try:
            from helpers.discord_followup import send_followup_message
            error_context = "updating your resume" if command_type == 'update' else "analyzing your resume"
            error_msg = f"An error occurred while {error_context}. 😔"
            send_followup_message(application_id, interaction_token, error_msg)
        except Exception as followup_error:
            logger.error(f"Failed to send error followup message: {str(followup_error)}")


def handle_async_command_local(raw_request, command_type):
    """
    Handle async commands in local development environment using background threads.
    
    Args:
        raw_request: Discord interaction data
        command_type: Type of async command ('update' or 'ai_review')
    
    Returns:
        Deferred response or error embed
    """
    logger.info(f"Command '{command_type}' will be processed in background thread (local mode)")
    
    try:
        application_id = raw_request.get('application_id')
        interaction_token = raw_request.get('token')
        
        if not application_id or not interaction_token:
            logger.error("Missing application_id or interaction_token for local async processing")
            return create_error_embed(
                "Processing Error",
                "Missing required Discord interaction data."
            )
        
        # Start background thread for async processing
        thread = threading.Thread(
            target=process_async_command_thread,
            args=(raw_request, command_type, application_id, interaction_token)
        )
        thread.daemon = True  # Thread will die when main process exits
        thread.start()
        
        logger.info(f"Background thread started for '{command_type}' command")
        return create_deferred_response()
        
    except Exception as e:
        logger.error(f"Failed to start background thread for '{command_type}': {str(e)}")
        return create_error_embed(
            "Processing Error",
            "Failed to start processing your request. Please try again."
        )