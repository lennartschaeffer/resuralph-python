import logging
from aws.s3 import save_s3_resume, delete_s3_resume
from aws.dynamo import save_db_resume, get_latest_db_resume
from helpers.validate_pdf import validate_pdf, PDFValidationError, validate_attachment_data
from helpers.embed_helper import create_success_embed, create_error_embed, create_info_embed

logger = logging.getLogger(__name__)


def handle_upload_command(interaction_data):
    
    try:
        user_id = interaction_data['member']['user']['id']
        logger.info(f"Processing upload command for user {user_id}")
        
        # check for existing resume
        existing_resume = get_latest_db_resume(user_id)
        if existing_resume and len(existing_resume) > 0:
            logger.info(f"User {user_id} already has existing resume, redirecting to update command")
            return create_info_embed(
                "Resume Already Exists",
                "It seems like you've already uploaded a resume before. Please use the `/update` command instead to update it."
            )
        
        attachment, error_message = validate_attachment_data(interaction_data, user_id)
        if error_message or not attachment:
            return create_error_embed(
                "Invalid Attachment",
                error_message or "Failed to extract attachment data."
            )

        # validate pdf
        try:
            file_bytes = validate_pdf(attachment.to_dict())
            logger.info(f"PDF validation successful for user {user_id}: {len(file_bytes)} bytes")
        except PDFValidationError as e:
            logger.warning(f"PDF validation failed for user {user_id}: {str(e)}")
            return create_error_embed(
                "PDF Validation Failed",
                f"PDF validation failed: {str(e)}"
            )
        
        # upload to S3
        logger.info(f"Uploading PDF to S3 for user {user_id}")
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
        
        # save to DynamoDB
        logger.info(f"Saving metadata to DynamoDB for user {user_id}")
        success = save_db_resume(pdf_url, attachment.filename, user_id, "v1")
        if not success:
            logger.error(f"DynamoDB save failed for user {user_id}, cleaning up S3 file")
            # cleanup S3 file if DB save failed
            delete_s3_resume(s3_key)
            return create_error_embed(
                "Save Failed",
                "Failed to save resume metadata. 😔"
            )
        
        # generate Hypothes.is annotation link
        annotation_link = f"https://via.hypothes.is/{pdf_url}"
        logger.info(f"Upload workflow completed successfully for user {user_id}")
        
        fields = [
            {
                "name": "🔗 Resume PDF Link",
                "value": f"[Click here to review and annotate]({annotation_link})",
                "inline": False
            }
        ]
        
        return create_success_embed(
            "Resume is Ready For Annotation!",
            "Your PDF has been successfully uploaded and is ready for review!",
            fields
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in upload workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return create_error_embed(
            "Unexpected Error",
            "An error occurred while processing your PDF. 😔"
        )