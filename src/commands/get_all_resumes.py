import os
import logging
from db.supabase_client import supabase_manager
from helpers.embed_helper import create_error_embed, create_info_embed

logger = logging.getLogger(__name__)

SITE_URL = os.environ.get("SITE_URL", "")


def handle_get_all_resumes_command(interaction_data):

    try:
        user_id = interaction_data.get('member', {}).get('user', {}).get('id')

        if not user_id:
            logger.error("Could not extract user ID from interaction data")
            return create_error_embed(
                "Processing Error",
                "An error occurred while processing your request."
            )

        logger.info(f"Getting all resumes for user {user_id}")

        all_docs = supabase_manager.get_documents_by_uploader(user_id)

        if not all_docs:
            return create_info_embed(
                "No Resumes Found",
                "It seems you haven't uploaded any resumes yet. Please use `/upload` first."
            )

        fields = []
        for doc in all_docs:
            version = doc['version']
            doc_id = doc['id']
            title = doc.get('title', 'Untitled')
            created_at = doc.get('createdAt', 'Unknown date')

            viewer_link = f"{SITE_URL}/view/{doc_id}"

            display_date = created_at[:10] if len(created_at) >= 10 else created_at

            fields.append({
                "name": f"Version {version} — {title}",
                "value": f"[View & Annotate]({viewer_link})\nUploaded: {display_date}",
                "inline": False
            })

        return create_info_embed(
            "All Your Resumes",
            f"Here are all {len(all_docs)} of your uploaded resume versions:",
            fields
        )

    except Exception as error:
        logger.error(f"Error getting all resumes: {str(error)}")
        return create_error_embed(
            "Error Retrieving Resumes",
            "An error occurred while getting your resumes."
        )
