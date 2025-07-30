import logging
from aws.s3 import save_s3_resume
from aws.dynamo import get_latest_db_resume, update_db_resume
from helpers.validate_pdf import validate_pdf, validate_attachment_data, PDFValidationError
from helpers.get_pdf_diff import compare_text_diff
from helpers.embed_helper import create_success_embed, create_error_embed, create_info_embed

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
    
    try:
        diff_result = compare_text_diff(old_resume_url, new_resume_url)
        added_text = diff_result.get('added_text')
        removed_text = diff_result.get('removed_text')
        
        embed = {
            "color": 0x0099ff,  
            "title": "📝 Resume Changes",
            "description": "See what was added and removed from your resume:",
            "footer": {
                "text": "🤖 ResuRalph by @Lenny"
            },
            "fields": []
        }
        
        # Handle case where no changes were found
        if not added_text and not removed_text:
            embed["description"] = "No changes were found in the resume."
            embed["color"] = 0xffff00  # Yellow color for no changes
            return {"embeds": [embed]}
        
        if added_text:
            added_field = {
                "name": "🟢 Added",
                "value": f"```{added_text[:1000]}```" if len(added_text) <= 1000 else f"```{added_text[:997]}```...",
                "inline": False
            }
        else:
            added_field = {
                "name": "🟢 Added", 
                "value": "No new content added.",
                "inline": False
            }
        embed["fields"].append(added_field)
        
        if removed_text:
            removed_field = {
                "name": "🔴 Removed",
                "value": f"```{removed_text[:1000]}```" if len(removed_text) <= 1000 else f"```{removed_text[:997]}```...",
                "inline": False
            }
        else:
            removed_field = {
                "name": "🔴 Removed",
                "value": "No content removed.",
                "inline": False
            }
        embed["fields"].append(removed_field)
        
        return {"embeds": [embed]}
        
    except Exception as e:
        logger.error(f"Error creating resume diff response: {str(e)}")

        error_embed = {
            "color": 0xff0000,  
            "title": "❌ Error",
            "description": "An error occurred while comparing the resume differences. 😔",
            "footer": {
                "text": "🤖 ResuRalph by @Lenny"
            }
        }
        return {"embeds": [error_embed]}


def handle_update_command(interaction_data):
   
    try:
        user_id = interaction_data['member']['user']['id']
        logger.info(f"Processing update command for user {user_id}")
        
        # Check if user has existing resume
        existing_resume = get_latest_db_resume(user_id)
        if not existing_resume or len(existing_resume) == 0:
            logger.warning(f"User {user_id} has no existing resume for update")
            return create_info_embed(
                "No Resume to Update",
                "It seems you haven't uploaded a resume yet. Please upload one first before updating."
            )
        
        # Get the current resume URL for diff comparison
        old_resume_url = existing_resume[0]['resume_url']
        logger.info(f"Found existing resume for user {user_id}: {old_resume_url}")
        
        # Validate attachment data
        attachment, error_message = validate_attachment_data(interaction_data, user_id)
        if error_message or not attachment:
            return create_error_embed(
                "Invalid Attachment",
                error_message or "Failed to extract attachment data."
            )

        # Validate PDF
        try:
            file_bytes = validate_pdf(attachment.to_dict())
            logger.info(f"PDF validation successful for user {user_id}: {len(file_bytes)} bytes")
        except PDFValidationError as e:
            logger.warning(f"PDF validation failed for user {user_id}: {str(e)}")
            return create_error_embed(
                "PDF Validation Failed",
                f"PDF validation failed: {str(e)}"
            )
        
        # Upload to S3
        logger.info(f"Uploading updated PDF to S3 for user {user_id}")
        s3_result = save_s3_resume(file_bytes, user_id)
        if not s3_result:
            logger.error(f"S3 upload failed for user {user_id}")
            return create_error_embed(
                "Upload Failed",
                "Failed to upload PDF to storage. 😔"
            )
        
        s3_key = s3_result['key']
        pdf_url = s3_result['pdf_url']
        logger.info(f"S3 upload successful for user {user_id}: {s3_key}")
        
        # Update DynamoDB with new version
        logger.info(f"Updating resume metadata in DynamoDB for user {user_id}")
        new_version = update_db_resume(user_id, pdf_url, attachment.filename)
        if not new_version:
            logger.error(f"DynamoDB update failed for user {user_id}")
            return create_error_embed(
                "Update Failed",
                "Failed to update resume metadata. 😔"
            )
        
        # Generate Hypothes.is annotation link
        annotation_link = f"https://via.hypothes.is/{pdf_url}"
        
        # Check if user wants to see diff
        show_diff = get_show_diff_option(interaction_data)
        
        if not show_diff:
            logger.info(f"Update workflow completed successfully for user {user_id} (no diff requested)")
            fields = [
                {
                    "name": "🔗 Resume PDF Link",
                    "value": f"[Click here to review and annotate]({annotation_link})",
                    "inline": False
                }
            ]
            return create_success_embed(
                "Resume Updated",
                "Your resume has been successfully updated!",
                fields
            )
        
        # Generate diff response
        logger.info(f"Generating diff comparison for user {user_id}")
        diff_response = create_resume_diff_response(old_resume_url, pdf_url)
        
        # Add annotation link to the embed
        if "embeds" in diff_response and len(diff_response["embeds"]) > 0:
            # Add annotation link as a field to the embed
            annotation_field = {
                "name": "🔗 Review Link",
                "value": f"[Click here to review and annotate]({annotation_link})",
                "inline": False
            }
            diff_response["embeds"][0]["fields"].append(annotation_field)
        
        logger.info(f"Update workflow with diff completed successfully for user {user_id}")
        return diff_response
        
    except Exception as e:
        logger.error(f"Unexpected error in update workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return create_error_embed(
            "Update Error",
            "An error occurred while updating your resume. 😔"
        )