import logging
from helpers.get_pdf_diff import compare_text_diff
from helpers.embed_helper import create_error_embed, create_info_embed

logger = logging.getLogger(__name__)


def extract_resume_urls(interaction_data):
    """Extract old_resume_url and new_resume_url from Discord interaction data"""
    data = interaction_data['data']
    
    if 'options' not in data:
        return None, None
    
    old_url = None
    new_url = None
    
    for option in data['options']:
        if option['name'] == 'old_resume_url':
            old_url = option.get('value')
        elif option['name'] == 'new_resume_url':
            new_url = option.get('value')
    
    return old_url, new_url


def create_resume_diff_response(old_resume_url, new_resume_url):
    """
    Generate a Discord embed response with resume differences
    
    Args:
        old_resume_url (str): URL of the previous resume
        new_resume_url (str): URL of the new resume
        
    Returns:
        dict: Discord embed response data
    """
    try:
        diff_result = compare_text_diff(old_resume_url, new_resume_url)
        added_text = diff_result.get('added_text')
        removed_text = diff_result.get('removed_text')
        
        # Create embed structure
        embed = {
            "color": 0x0099ff,  # Blue color
            "title": "📝 Resume Changes",
            "description": "See what was added and removed from your resume:",
            "footer": {
                "text": "🤖 ResuRalph by @Lenny"
            },
            "fields": []
        }
        
        # Handle case where no changes were found
        if not added_text and not removed_text:
            embed["description"] = "No changes were found between the two resumes."
            embed["color"] = 0xffff00  # Yellow color for no changes
            return {"embeds": [embed]}
        
        # Add "Added" field
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
        
        # Add "Removed" field
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
        # Return error embed
        error_embed = {
            "color": 0xff0000,  # Red color for error
            "title": "❌ Error",
            "description": "An error occurred while comparing the resume differences. 😔",
            "footer": {
                "text": "🤖 ResuRalph by @Lenny"
            }
        }
        return {"embeds": [error_embed]}


def handle_get_resume_diff_command(interaction_data):
    """
    Handle the /get_resume_diff command workflow
    
    Args:
        interaction_data (dict): Discord interaction data
        
    Returns:
        dict: Response message for Discord
    """
    try:
        user_id = interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')
        logger.info(f"Processing get_resume_diff command for user {user_id}")
        
        # Extract URLs from interaction data
        old_url, new_url = extract_resume_urls(interaction_data)
        
        if not old_url or not new_url:
            logger.warning(f"Missing URLs for user {user_id}: old={old_url}, new={new_url}")
            return create_error_embed(
                "Missing URLs",
                "Please provide both old_resume_url and new_resume_url parameters."
            )
        
        # Remove hypothesis prefix to get clean PDF URLs
        clean_old_url = old_url.replace("https://via.hypothes.is/", "")
        clean_new_url = new_url.replace("https://via.hypothes.is/", "")
        
        logger.info(f"Comparing resumes for user {user_id}: {clean_old_url} vs {clean_new_url}")
        
        # Generate diff response
        diff_response = create_resume_diff_response(clean_old_url, clean_new_url)
        
        logger.info(f"Resume diff completed successfully for user {user_id}")
        return diff_response
        
    except Exception as e:
        logger.error(f"Unexpected error in get_resume_diff workflow for user {interaction_data.get('member', {}).get('user', {}).get('id', 'unknown')}: {str(e)}")
        return create_error_embed(
            "Diff Error",
            "An error occurred while comparing your resumes. 😔"
        )