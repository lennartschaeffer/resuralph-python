import logging
from aws.s3 import save_s3_resume, delete_s3_resume
from aws.dynamo import save_db_resume, get_latest_db_resume
from helpers.validate_pdf import validate_pdf, PDFValidationError
from models.resume import DiscordAttachment

logger = logging.getLogger(__name__)


def validate_attachment_data(interaction_data, user_id):
    data = interaction_data['data']
    
    if 'resolved' not in data or 'attachments' not in data['resolved']:
        logger.warning(f"No attachment found in request for user {user_id}")
        return None, "No file attachment found. Please attach a PDF file."
    
    attachment_id = None
    if 'options' in data:
        for option in data['options']:
            if option['name'] == 'file':
                attachment_id = option['value']
                break
    
    if not attachment_id:
        logger.warning(f"No attachment ID found in options for user {user_id}")
        return None, "No file attachment found in command options."
    
    attachments = data['resolved']['attachments']
    if attachment_id not in attachments:
        logger.error(f"Attachment {attachment_id} not found in resolved data for user {user_id}")
        return None, "Attachment not found in resolved data."
    
    attachment_data = attachments[attachment_id]
    attachment = DiscordAttachment.from_discord_data(attachment_data)
    logger.info(f"Processing attachment: {attachment.filename} ({attachment.size_mb():.1f}MB) for user {user_id}")
    
    return attachment, None


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
        
        # check for existing resume
        existing_resume = get_latest_db_resume(user_id)
        if existing_resume and len(existing_resume) > 0:
            logger.info(f"User {user_id} already has existing resume, redirecting to update command")
            return "Hmm, it seems like you've already uploaded a resume before. Please use the /update command instead to update it."
        
        attachment, error_message = validate_attachment_data(interaction_data, user_id)
        if error_message or not attachment:
            return error_message or "Failed to extract attachment data."

        # validate pdf
        try:
            file_bytes = validate_pdf(attachment.to_dict())
            logger.info(f"PDF validation successful for user {user_id}: {len(file_bytes)} bytes")
        except PDFValidationError as e:
            logger.warning(f"PDF validation failed for user {user_id}: {str(e)}")
            return f"PDF validation failed: {str(e)}"
        
        # upload to S3
        logger.info(f"Uploading PDF to S3 for user {user_id}")
        s3_result = save_s3_resume(file_bytes, user_id)
        if not s3_result:
            logger.error(f"S3 upload failed for user {user_id}")
            return "Failed to upload PDF to storage. 😔"
        
        s3_key = s3_result['key']
        pdf_url = s3_result['pdf_url']
        logger.info(f"S3 upload successful for user {user_id}: {s3_key}")
        
        # save to DynamoDB
        logger.info(f"Saving metadata to DynamoDB for user {user_id}")
        success = save_db_resume(pdf_url, attachment.filename, user_id, "v1")
        if not success:
            logger.error(f"DynamoDB save failed for user {user_id}, cleaning up S3 file")
            # cleanup S3 file if DB save failed
            delete_s3_resume(s3_key)
            return "Failed to save resume metadata. 😔"
        
        # generate Hypothes.is annotation link
        annotation_link = f"https://via.hypothes.is/{pdf_url}"
        logger.info(f"Upload workflow completed successfully for user {user_id}")
        
        return f"📝 Your PDF is ready for annotation: {annotation_link}"
        
    except Exception as e:
        logger.error(f"Unexpected error in upload workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return "An error occurred while processing your PDF. 😔"