import logging
from aws.s3 import save_s3_resume, delete_s3_resume
from aws.dynamo import save_db_resume, get_latest_db_resume
from helpers.validate_pdf import validate_pdf, PDFValidationError
from models.resume import DiscordAttachment

logger = logging.getLogger(__name__)


def handle_upload_command(interaction_data):
    """
    Handle the /upload command workflow
    
    Args:
        interaction_data (dict): Discord interaction data
        
    Returns:
        str: Response message for Discord
    """
    try:
        user_id = interaction_data['member']['user']['id']
        logger.info(f"Processing upload command for user {user_id}")
        
        # Check if user already has a resume (they should use /update instead)
        existing_resume = get_latest_db_resume(user_id)
        if existing_resume and len(existing_resume) > 0:
            logger.info(f"User {user_id} already has existing resume, redirecting to update command")
            return "Hmm, it seems like you've already uploaded a resume before. Please use the /update command instead to update it."
        
        # Extract attachment information from Discord data
        data = interaction_data['data']
        if 'resolved' not in data or 'attachments' not in data['resolved']:
            logger.warning(f"No attachment found in request for user {user_id}")
            return "No file attachment found. Please attach a PDF file."
        
        # Get the attachment ID from options
        attachment_id = None
        if 'options' in data:
            for option in data['options']:
                if option['name'] == 'file':
                    attachment_id = option['value']
                    break
        
        if not attachment_id:
            logger.warning(f"No attachment ID found in options for user {user_id}")
            return "No file attachment found in command options."
        
        # Get attachment details
        attachments = data['resolved']['attachments']
        if attachment_id not in attachments:
            logger.error(f"Attachment {attachment_id} not found in resolved data for user {user_id}")
            return "Attachment not found in resolved data."
        
        attachment_data = attachments[attachment_id]
        attachment = DiscordAttachment.from_discord_data(attachment_data)
        logger.info(f"Processing attachment: {attachment.filename} ({attachment.size_mb():.1f}MB) for user {user_id}")
        
        # Validate the PDF
        try:
            file_bytes = validate_pdf(attachment.to_dict())
            logger.info(f"PDF validation successful for user {user_id}: {len(file_bytes)} bytes")
        except PDFValidationError as e:
            logger.warning(f"PDF validation failed for user {user_id}: {str(e)}")
            return f"PDF validation failed: {str(e)}"
        
        # Upload to S3
        logger.info(f"Uploading PDF to S3 for user {user_id}")
        s3_result = save_s3_resume(file_bytes, user_id)
        if not s3_result:
            logger.error(f"S3 upload failed for user {user_id}")
            return "Failed to upload PDF to storage. 😔"
        
        s3_key = s3_result['key']
        pdf_url = s3_result['pdf_url']
        logger.info(f"S3 upload successful for user {user_id}: {s3_key}")
        
        # Save to DynamoDB
        logger.info(f"Saving metadata to DynamoDB for user {user_id}")
        success = save_db_resume(pdf_url, attachment.filename, user_id, "v1")
        if not success:
            logger.error(f"DynamoDB save failed for user {user_id}, cleaning up S3 file")
            # Cleanup S3 file if DB save failed
            delete_s3_resume(s3_key)
            return "Failed to save resume metadata. 😔"
        
        # Generate Hypothes.is annotation link
        annotation_link = f"https://via.hypothes.is/{pdf_url}"
        logger.info(f"Upload workflow completed successfully for user {user_id}")
        
        return f"📝 Your PDF is ready for annotation: {annotation_link}"
        
    except Exception as e:
        logger.error(f"Unexpected error in upload workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return "An error occurred while processing your PDF. 😔"