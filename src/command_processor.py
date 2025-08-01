import json
import logging
from typing import Dict, Any, List
from helpers.discord_followup import send_followup_message

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # AWS Lambda handler for processing Discord commands from SQS messages.
    try:
        logger.info(f"Processing {len(event['Records'])} command(s) from SQS")
        
        results = []
        for record in event['Records']: # SQS event containing command processing jobs
            result = process_sqs_record(record)
            results.append(result)
        
        logger.info(f"Completed processing {len(results)} command(s)")
        return {
            'statusCode': 200,
            'processedCount': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in command processor handler: {str(e)}")
        raise


def process_sqs_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes a single SQS record containing a command processing job.
    
    Args:
        record: SQS record with command data
    
    Returns:
        Dict: Processing result
    """
    try:
        # Parse message body
        message_body = json.loads(record['body'])
        interaction_data = message_body['interaction_data']
        command_type = message_body['command_type']
        application_id = message_body['application_id']
        interaction_token = message_body['interaction_token']
        
        logger.info(f"Processing {command_type} command from SQS")
        
        # Validate required data
        if not application_id or not interaction_token:
            error_msg = "Missing application_id or interaction_token in SQS message"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Process the command
        result_message = process_command(interaction_data, command_type)
        
        # Send follow-up message to Discord
        success = send_followup_message(application_id, interaction_token, result_message)
        
        if not success:
            # Try to send error message if main result failed
            error_msg = f"An error occurred while processing your {command_type}. Please try again."
            send_followup_message(application_id, interaction_token, error_msg)
            return {'success': False, 'command_type': command_type, 'error': 'Failed to send follow-up message'}
        
        logger.info(f"Successfully processed {command_type} command")
        return {'success': True, 'command_type': command_type}
        
    except Exception as e:
        logger.error(f"Error processing SQS record: {str(e)}")
        return {'success': False, 'error': str(e)}


def process_command(interaction_data: Dict[str, Any], command_type: str) -> Any:
    """
    Processes the actual command and returns the result message.
    
    Args:
        interaction_data: Discord interaction data
        command_type: Type of command to process
    
    Returns:
        The result message to send back to Discord
    """
    try:
        if command_type == 'update':
            from commands.update import handle_update_command
            return handle_update_command(interaction_data)
        elif command_type == 'ai_review':
            from commands.ai_review import handle_ai_review_command
            return handle_ai_review_command(interaction_data)
        else:
            raise ValueError(f"Unknown command type: {command_type}")
            
    except Exception as e:
        logger.error(f"Error processing {command_type} command: {str(e)}")
        error_context = "updating your resume" if command_type == 'update' else "analyzing your resume"
        return f"An error occurred while {error_context}. 😔"