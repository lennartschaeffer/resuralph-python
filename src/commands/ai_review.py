import logging
from helpers.embed_helper import create_info_embed

logger = logging.getLogger(__name__)


def handle_ai_review_command(interaction_data):

    user_id = interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')
    logger.info(f"AI review requested by user {user_id} — feature currently disabled")

    return create_info_embed(
        "AI Review Temporarily Disabled",
        "The AI review feature is currently disabled and will be back soon. Stay tuned!"
    )
