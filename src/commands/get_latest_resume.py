import logging
from aws.dynamo import get_latest_db_resume

logger = logging.getLogger(__name__)


def handle_get_latest_resume_command(interaction_data):
    """
    Handle the /get_latest_resume command
    
    Args:
        interaction_data (dict): Discord interaction data
        
    Returns:
        str: Response message for the user
    """
    try:
        # Extract user ID from interaction data
        user_id = interaction_data.get('member', {}).get('user', {}).get('id')
        
        if not user_id:
            logger.error("Could not extract user ID from interaction data")
            return "An error occurred while processing your request. 😔"
        
        logger.info(f"Getting latest resume for user {user_id}")
        
        # Get the latest resume from DynamoDB
        latest_resume = get_latest_db_resume(user_id)
        
        if not latest_resume or len(latest_resume) == 0:
            return "It seems you haven't uploaded a resume yet. Please upload one first before requesting the latest one."
        
        # Extract the resume URL from the first (latest) result
        latest_resume_url = latest_resume[0]['resume_url']
        
        # Generate Hypothes.is annotation URL
        hypothesis_url = f"https://via.hypothes.is/{latest_resume_url}"
        
        return f"📝 Here's the link to your latest resume: {hypothesis_url}"
        
    except Exception as error:
        logger.error(f"Error getting latest resume: {str(error)}")
        return "An error occurred while getting your resume. 😔"