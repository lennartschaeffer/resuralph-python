import os
import logging
from db.supabase_client import supabase_manager
from helpers.embed_helper import create_error_embed, create_info_embed

logger = logging.getLogger(__name__)

SITE_URL = os.environ.get("SITE_URL", "")


def handle_get_latest_resume_command(interaction_data):

    try:
        user_id = interaction_data.get('member', {}).get('user', {}).get('id')

        if not user_id:
            logger.error("Could not extract user ID from interaction data")
            return create_error_embed(
                "Processing Error",
                "An error occurred while processing your request."
            )

        logger.info(f"Getting latest resume for user {user_id}")

        latest_doc = supabase_manager.get_latest_document(user_id)

        if not latest_doc:
            return create_info_embed(
                "No Resume Found",
                "It seems you haven't uploaded a resume yet. Please use `/upload` first."
            )

        viewer_link = f"{SITE_URL}/view/{latest_doc['id']}"

        fields = [
            {
                "name": "Latest Resume",
                "value": f"[Click here to view and annotate]({viewer_link})",
                "inline": False
            }
        ]

        return create_info_embed(
            "Latest Resume",
            f"Here's the link to your latest resume (version {latest_doc['version']}):",
            fields
        )

    except Exception as error:
        logger.error(f"Error getting latest resume: {str(error)}")
        return create_error_embed(
            "Error Retrieving Resume",
            "An error occurred while getting your resume."
        )
