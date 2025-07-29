import logging
from aws.s3 import save_s3_resume
from aws.dynamo import get_latest_db_resume, update_db_resume
from helpers.validate_pdf import validate_pdf, validate_attachment_data, PDFValidationError
from helpers.get_pdf_diff import compare_text_diff

logger = logging.getLogger(__name__)


def get_show_diff_option(interaction_data):
    """Extract the show_diff boolean option from Discord interaction data"""
    data = interaction_data['data']
    
    if 'options' not in data:
        return False
    
    for option in data['options']:
        if option['name'] == 'show_diff':
            return option.get('value', False)
    
    return False


def create_resume_diff_response(old_resume_url, new_resume_url):
    """
    Generate a formatted response with resume differences
    
    Args:
        old_resume_url (str): URL of the previous resume
        new_resume_url (str): URL of the new resume
        
    Returns:
        str: Formatted response message with differences
    """
    try:
        diff_result = compare_text_diff(old_resume_url, new_resume_url)
        added_text = diff_result.get('added_text')
        removed_text = diff_result.get('removed_text')
        
        if not added_text and not removed_text:
            return "No changes were found in the resume."
        
        # Format response with Discord-style formatting
        response_parts = ["📝 **Resume Changes**", "See what was added and removed from your resume:", ""]
        
        if added_text:
            response_parts.extend([
                "🟢 **Added:**",
                f"```{added_text}```",
                ""
            ])
        else:
            response_parts.extend([
                "🟢 **Added:**",
                "No new content added.",
                ""
            ])
        
        if removed_text:
            response_parts.extend([
                "🔴 **Removed:**",
                f"```{removed_text}```",
                ""
            ])
        else:
            response_parts.extend([
                "🔴 **Removed:**", 
                "No content removed.",
                ""
            ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error creating resume diff response: {str(e)}")
        return "An error occurred while comparing the resume differences. 😔"


def handle_update_command(interaction_data):
    """
    Handle the /update command workflow
    
    Args:
        interaction_data (dict): Discord interaction data
        
    Returns:
        str: Response message for Discord
    """
    try:
        user_id = interaction_data['member']['user']['id']
        logger.info(f"Processing update command for user {user_id}")
        
        # Check if user has existing resume
        existing_resume = get_latest_db_resume(user_id)
        if not existing_resume or len(existing_resume) == 0:
            logger.warning(f"User {user_id} has no existing resume for update")
            return "It seems you haven't uploaded a resume yet. Please upload one first before updating."
        
        # Get the current resume URL for diff comparison
        old_resume_url = existing_resume[0]['resume_url']
        logger.info(f"Found existing resume for user {user_id}: {old_resume_url}")
        
        # Validate attachment data
        attachment, error_message = validate_attachment_data(interaction_data, user_id)
        if error_message or not attachment:
            return error_message or "Failed to extract attachment data."

        # Validate PDF
        try:
            file_bytes = validate_pdf(attachment.to_dict())
            logger.info(f"PDF validation successful for user {user_id}: {len(file_bytes)} bytes")
        except PDFValidationError as e:
            logger.warning(f"PDF validation failed for user {user_id}: {str(e)}")
            return f"PDF validation failed: {str(e)}"
        
        # Upload to S3
        logger.info(f"Uploading updated PDF to S3 for user {user_id}")
        s3_result = save_s3_resume(file_bytes, user_id)
        if not s3_result:
            logger.error(f"S3 upload failed for user {user_id}")
            return "Failed to upload PDF to storage. 😔"
        
        s3_key = s3_result['key']
        pdf_url = s3_result['pdf_url']
        logger.info(f"S3 upload successful for user {user_id}: {s3_key}")
        
        # Update DynamoDB with new version
        logger.info(f"Updating resume metadata in DynamoDB for user {user_id}")
        new_version = update_db_resume(user_id, pdf_url, attachment.filename)
        if not new_version:
            logger.error(f"DynamoDB update failed for user {user_id}")
            return "Failed to update resume metadata. 😔"
        
        # Generate Hypothes.is annotation link
        annotation_link = f"https://via.hypothes.is/{pdf_url}"
        
        # Check if user wants to see diff
        show_diff = get_show_diff_option(interaction_data)
        
        if not show_diff:
            logger.info(f"Update workflow completed successfully for user {user_id} (no diff requested)")
            return f"📝 Your Resume has been updated! Here's the new link for review: {annotation_link}"
        
        # Generate diff response
        logger.info(f"Generating diff comparison for user {user_id}")
        diff_response = create_resume_diff_response(old_resume_url, pdf_url)
        
        # Combine diff with annotation link
        full_response = f"{diff_response}\n\nHere's the new link for review: {annotation_link}"
        
        logger.info(f"Update workflow with diff completed successfully for user {user_id}")
        return full_response
        
    except Exception as e:
        logger.error(f"Unexpected error in update workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return "An error occurred while updating your resume. 😔"