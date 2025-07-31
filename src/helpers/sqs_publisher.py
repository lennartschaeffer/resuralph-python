import json
import logging
import boto3
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

def publish_command_to_queue(interaction_data: Dict[str, Any], command_type: str) -> bool:
    """
    Publishes a command processing job to the SQS queue for async execution.
    
    Args:
        interaction_data: The Discord interaction data
        command_type: The type of command to process ('update', 'ai_review', etc.)
    
    Returns:
        bool: True if message was published successfully, False otherwise
    """
    try:
        queue_url = os.getenv('COMMAND_QUEUE_URL')
        if not queue_url:
            logger.error("COMMAND_QUEUE_URL environment variable not set")
            return False
            
        sqs_client = boto3.client('sqs')
        
        # Prepare message payload
        message_body = {
            'interaction_data': interaction_data,
            'command_type': command_type,
            'application_id': interaction_data.get('application_id'),
            'interaction_token': interaction_data.get('token')
        }
        
        # Send message to SQS
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                'command_type': {
                    'StringValue': command_type,
                    'DataType': 'String'
                }
            }
        )
        
        logger.info(f"Command '{command_type}' queued successfully. MessageId: {response['MessageId']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to queue command '{command_type}': {str(e)}")
        return False


def create_deferred_response() -> Dict[str, Any]:
    """
    Creates a Discord deferred response indicating processing is happening in background.
    
    Returns:
        Dict: Discord deferred response payload
    """
    return {
        "type": 5  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
    }