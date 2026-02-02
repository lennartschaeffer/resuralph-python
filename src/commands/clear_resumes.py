import logging
from aws.s3 import delete_s3_resume
from db.supabase_client import supabase_manager
from helpers.embed_helper import create_success_embed, create_error_embed, create_info_embed, create_warning_embed

logger = logging.getLogger(__name__)


def handle_clear_resumes_command(interaction_data):

    try:
        user_id = interaction_data['member']['user']['id']
        logger.info(f"Processing clear_resumes command for user {user_id}")

        existing_docs = supabase_manager.get_documents_by_uploader(user_id)
        if not existing_docs:
            logger.info(f"User {user_id} has no resumes to clear")
            return create_info_embed(
                "No Resumes Found",
                "You don't have any resumes to clear."
            )

        doc_count = len(existing_docs)
        logger.info(f"User {user_id} has {doc_count} resumes to clear")

        # Delete S3 objects for each document
        s3_failures = 0
        for doc in existing_docs:
            s3_key = doc.get('s3Key')
            if s3_key:
                success = delete_s3_resume(s3_key)
                if not success:
                    s3_failures += 1
                    logger.warning(f"Failed to delete S3 object {s3_key} for user {user_id}")

        # Delete documents from Supabase (cascade deletes annotations)
        db_failures = 0
        for doc in existing_docs:
            success = supabase_manager.delete_document(doc['id'])
            if not success:
                db_failures += 1
                logger.error(f"Failed to delete document {doc['id']} for user {user_id}")

        if db_failures > 0:
            logger.error(f"{db_failures} document deletions failed for user {user_id}")
            return create_error_embed(
                "Clear Partially Failed",
                f"Failed to clear {db_failures} of {doc_count} resume records. Please try again."
            )

        if s3_failures > 0:
            logger.warning(f"{s3_failures} S3 deletions failed for user {user_id}, but DB records cleared")
            return create_warning_embed(
                "Partial Clear Complete",
                f"Successfully cleared {doc_count} resume records, but some files may remain in storage."
            )

        logger.info(f"Clear workflow completed successfully for user {user_id}")
        return create_success_embed(
            "All Resumes Cleared",
            f"Successfully cleared all {doc_count} of your resumes."
        )

    except Exception as e:
        logger.error(f"Unexpected error in clear_resumes workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return create_error_embed(
            "Clear Failed",
            "An error occurred while clearing your resumes. Please try again later."
        )
