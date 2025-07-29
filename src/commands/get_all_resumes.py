import logging
from aws.dynamo import get_all_user_resumes
from helpers.embed_helper import create_error_embed, create_info_embed

logger = logging.getLogger(__name__)


def handle_get_all_resumes_command(interaction_data):
    """
    Handle the /get_all_resumes command
    
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
            return create_error_embed(
                "Processing Error",
                "An error occurred while processing your request. 😔"
            )
        
        logger.info(f"Getting all resumes for user {user_id}")
        
        # Get all resumes from DynamoDB
        all_resumes = get_all_user_resumes(user_id)
        
        if not all_resumes or len(all_resumes) == 0:
            return create_info_embed(
                "No Resumes Found",
                "It seems you haven't uploaded any resumes yet. Please upload one first."
            )
        
        # Create fields for each resume version
        fields = []
        for resume in all_resumes:
            version = resume['resume_version']
            resume_url = resume['resume_url']
            created_at = resume.get('created_at', 'Unknown date')
            
            # Generate Hypothes.is annotation URL
            hypothesis_url = f"https://via.hypothes.is/{resume_url}"
            
            fields.append({
                "name": f"📄 Resume {version}",
                "value": f"[View & Annotate]({hypothesis_url})\nUploaded: {created_at[:10]}",
                "inline": False
            })
        
        return create_info_embed(
            "All Your Resumes",
            f"Here are all {len(all_resumes)} of your uploaded resume versions:",
            fields
        )
        
    except Exception as error:
        logger.error(f"Error getting all resumes: {str(error)}")
        return create_error_embed(
            "Error Retrieving Resumes",
            "An error occurred while getting your resumes. 😔"
        )