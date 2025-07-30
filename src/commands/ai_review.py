import os
import logging
from helpers.embed_helper import create_error_embed, create_success_embed
from helpers.pdf_extractor import extract_text_from_pdf_url, clean_resume_text, validate_resume_content
from helpers.ai_resume_analyzer import analyze_resume_text, format_feedback_for_annotations
from helpers.hypothesis_client import create_bulk_annotations, validate_annotation_data
from aws.dynamo import get_latest_db_resume

logger = logging.getLogger(__name__)


def handle_ai_review_command(interaction_data):
    """
    Handle the /ai_review command
    
    Args:
        interaction_data (dict): Discord interaction data
        
    Returns:
        dict: Response message for Discord
    """
    try:
        user_id = interaction_data.get('member', {}).get('user', {}).get('id')
        if not user_id:
            logger.error("Could not extract user ID from interaction data")
            return create_error_embed(
                "Processing Error",
                "An error occurred while processing your request. 😔"
            )

        logger.info(f"Processing AI review request for user {user_id}")

        # Check for required API keys
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("OPENAI_API_KEY not configured")
            return create_error_embed(
                "Configuration Error",
                "AI review service is not properly configured. Please contact support. 🔧"
            )

        if not os.getenv('HYPOTHESIS_API_KEY'):
            logger.error("HYPOTHESIS_API_KEY not configured")
            return create_error_embed(
                "Configuration Error", 
                "Annotation service is not properly configured. Please contact support. 🔧"
            )

        # Get the latest resume for the user
        latest_resume = get_latest_db_resume(user_id)
        
        # Extract the resume URL from the first (latest) result
        latest_resume_url = latest_resume[0]['resume_url']
        if not latest_resume:
            logger.warning(f"No resume found for user {user_id}")
            return create_error_embed(
                "No Resume Found",
                "You don't have any resumes uploaded yet. Use `/upload` to upload your resume first! 📄"
            )

        logger.info(f"Found resume for user {user_id}: {latest_resume_url}")

        # Extract text from PDF
        resume_text = extract_text_from_pdf_url(latest_resume_url)
        if not resume_text:
            logger.error(f"Failed to extract text from PDF: {latest_resume_url}")
            return create_error_embed(
                "PDF Processing Error",
                "Unable to extract text from your resume. Please ensure it's a valid PDF with readable text. 📄"
            )

        # Clean and validate resume content
        cleaned_text = clean_resume_text(resume_text)
        if not validate_resume_content(cleaned_text):
            logger.warning(f"Resume content validation failed for user {user_id}")
            return create_error_embed(
                "Content Validation Error",
                "The uploaded file doesn't appear to contain resume content. Please upload a proper resume. 📄"
            )

        logger.info(f"Successfully extracted and validated resume text ({len(cleaned_text)} chars)")

        # Analyze resume with AI
        feedback_items = analyze_resume_text(cleaned_text)
        if not feedback_items:
            logger.error(f"AI analysis failed for user {user_id}")
            return create_error_embed(
                "AI Analysis Error",
                "Unable to analyze your resume at this time. Please try again later. 🤖"
            )

        logger.info(f"AI generated {len(feedback_items)} feedback items")

        # Get Hypothesis URL for annotations
        hypothesis_url = f"https://via.hypothes.is/{latest_resume_url}"
        
        # Format feedback for Hypothesis annotations
        annotations = format_feedback_for_annotations(feedback_items, hypothesis_url)
        
        # Validate annotations before sending
        valid_annotations = []
        for annotation in annotations:
            if validate_annotation_data(annotation):
                valid_annotations.append(annotation)
            else:
                logger.warning("Skipping invalid annotation data")

        if not valid_annotations:
            logger.error("No valid annotations generated")
            return create_error_embed(
                "Annotation Error",
                "Unable to create annotations for your resume. Please try again. 📝"
            )

        # Create annotations via Hypothesis API
        results = create_bulk_annotations(valid_annotations)
        
        # Check results and format response
        total_annotations = results['total']
        created_count = len(results['created'])
        failed_count = len(results['failed'])

        if created_count == 0:
            logger.error(f"All annotations failed to create for user {user_id}")
            return create_error_embed(
                "Annotation Creation Failed",
                "Unable to create annotations on your resume. Please try again later. 😔"
            )

        # Create success response
        success_message = f"✅ **AI Review Complete!**\n\n"
        success_message += f"📊 **Analysis Summary:**\n"
        success_message += f"• {created_count} annotations created\n"
        
        if failed_count > 0:
            success_message += f"• {failed_count} failed to create\n"
        
        success_message += f"\n🔗 **View Your Annotated Resume:**\n{hypothesis_url}\n\n"
        success_message += f"💡 **Tips:**\n"
        success_message += f"• Review each annotation carefully\n"
        success_message += f"• Look for strength indicators (💪) and improvement areas (🔧)\n"
        success_message += f"• Use suggestions (💡) to enhance your resume\n"

        embed = create_success_embed(
            "🤖 AI Resume Review Complete!",
            success_message
        )
        
        # Add hypothesis link as a field for easy access
        embed["fields"] = [{
            "name": "📝 View Annotated Resume",
            "value": f"[Click here to see your AI-reviewed resume]({hypothesis_url})",
            "inline": False
        }]

        logger.info(f"Successfully completed AI review for user {user_id}: {created_count}/{total_annotations} annotations created")
        return embed

    except Exception as e:
        logger.error(f"Error in ai_review command: {str(e)}")
        return create_error_embed(
            "AI Review Error",
            "An unexpected error occurred during AI review. Please try again later. 🤖"
        )