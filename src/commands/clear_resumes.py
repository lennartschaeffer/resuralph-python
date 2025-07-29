import logging
from aws.s3 import clear_all_user_s3_resumes
from aws.dynamo import clear_all_user_resumes, get_all_user_resumes
from helpers.embed_helper import create_success_embed, create_error_embed, create_info_embed, create_warning_embed

logger = logging.getLogger(__name__)


def handle_clear_resumes_command(interaction_data):
    """
    Handle the /clear_resumes command workflow
    
    Args:
        interaction_data (dict): Discord interaction data
        
    Returns:
        str: Response message for Discord
    """
    try:
        user_id = interaction_data['member']['user']['id']
        logger.info(f"Processing clear_resumes command for user {user_id}")
        
        # First check if user has any resumes
        existing_resumes = get_all_user_resumes(user_id)
        if not existing_resumes or len(existing_resumes) == 0:
            logger.info(f"User {user_id} has no resumes to clear")
            return create_info_embed(
                "No Resumes Found",
                "You don't have any resumes to clear. 📭"
            )
        
        resume_count = len(existing_resumes)
        logger.info(f"User {user_id} has {resume_count} resumes to clear")
        
        # Clear from DynamoDB first (safer to have orphaned S3 files than orphaned DB records)
        logger.info(f"Clearing DynamoDB records for user {user_id}")
        db_success = clear_all_user_resumes(user_id)
        if not db_success:
            logger.error(f"DynamoDB clear failed for user {user_id}")
            return create_error_embed(
                "Database Clear Failed",
                "Failed to clear resume metadata from database. Please try again later. 😔"
            )
        
        # Clear from S3
        logger.info(f"Clearing S3 objects for user {user_id}")
        s3_success = clear_all_user_s3_resumes(user_id)
        if not s3_success:
            logger.warning(f"S3 clear failed for user {user_id}, but DynamoDB was cleared")
            return create_warning_embed(
                "Partial Clear Complete",
                f"Successfully cleared {resume_count} resume records, but some files may remain in storage. Contact support if needed."
            )
        
        logger.info(f"Clear workflow completed successfully for user {user_id}")
        return create_success_embed(
            "All Resumes Cleared",
            f"Successfully cleared all {resume_count} of your resumes from the system. All data has been permanently deleted."
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in clear_resumes workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return create_error_embed(
            "Clear Failed",
            "An error occurred while clearing your resumes. Please try again later. 😔"
        )