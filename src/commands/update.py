import os
import uuid
import logging
from aws.s3 import save_s3_resume, delete_s3_resume
from db.supabase_client import supabase_manager
from helpers.validate_pdf import validate_pdf, validate_attachment_data, PDFValidationError
from helpers.embed_helper import create_success_embed, create_error_embed, create_info_embed

logger = logging.getLogger(__name__)

SITE_URL = os.environ.get("SITE_URL", "")


def handle_update_command(interaction_data):

    try:
        user_id = interaction_data['member']['user']['id']
        username = (
            interaction_data['member']['user'].get('global_name')
            or interaction_data['member']['user'].get('username', 'unknown')
        )
        logger.info(f"Processing update command for user {user_id}")

        # Check if user has existing documents
        existing_docs = supabase_manager.get_documents_by_uploader(user_id)
        if not existing_docs:
            logger.warning(f"User {user_id} has no existing resume for update")
            return create_info_embed(
                "No Resume to Update",
                "It seems you haven't uploaded a resume yet. Please use `/upload` first."
            )

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

        # Upload to private S3 bucket
        logger.info(f"Uploading updated PDF to S3 for user {user_id}")
        s3_key = save_s3_resume(file_bytes, user_id)
        if not s3_key:
            logger.error(f"S3 upload failed for user {user_id}")
            return create_error_embed(
                "Upload Failed",
                "Failed to upload PDF to storage."
            )
        logger.info(f"S3 upload successful for user {user_id}: {s3_key}")

        # Compute next version
        latest_version = supabase_manager.get_latest_version(user_id)
        next_version = latest_version + 1

        # Insert new document into Supabase — compensate by deleting S3 object on failure
        document_id = str(uuid.uuid4())
        title = attachment.filename
        try:
            doc = supabase_manager.insert_document(
                id=document_id,
                s3_key=s3_key,
                title=title,
                uploader_id=user_id,
                uploader_username=username,
                version=next_version,
            )
        except Exception:
            logger.error(f"Supabase insert failed for user {user_id}, cleaning up S3 object")
            delete_s3_resume(s3_key)
            raise

        if not doc:
            logger.error(f"Supabase insert returned no data for user {user_id}, cleaning up S3 object")
            delete_s3_resume(s3_key)
            return create_error_embed(
                "Save Failed",
                "Failed to save resume metadata."
            )

        viewer_link = f"{SITE_URL}/view/{document_id}"
        logger.info(f"Update workflow completed successfully for user {user_id} (version {next_version})")

        # TODO: Re-implement diff functionality (show_diff option) with private S3

        fields = [
            {
                "name": "Resume Link",
                "value": f"[Click here to review and annotate]({viewer_link})",
                "inline": False
            }
        ]
        return create_success_embed(
            "Resume Updated!",
            f"Your resume has been successfully updated to version {next_version}!",
            fields
        )

    except Exception as e:
        logger.error(f"Unexpected error in update workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return create_error_embed(
            "Update Error",
            "An error occurred while updating your resume."
        )
