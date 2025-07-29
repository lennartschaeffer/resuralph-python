import requests
import PyPDF2
from io import BytesIO
import logging
from models.resume import DiscordAttachment


logger = logging.getLogger(__name__)

class PDFValidationError(Exception):
    """Custom exception for PDF validation errors."""
    pass

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

def validate_pdf(attachment_info):
    """
    Validate and download a PDF attachment from Discord
    
    Args:
        attachment_info (dict): Discord attachment object containing:
            - content_type: MIME type
            - size: File size in bytes  
            - url: Download URL
            - filename: Original filename
            
    Returns:
        bytes: PDF file content as bytes
        
    Raises:
        PDFValidationError: If validation fails
    """
    try:
        # Check content type
        if attachment_info.get('content_type') != 'application/pdf':
            raise PDFValidationError(
                f"Invalid file type. Expected PDF, got {attachment_info.get('content_type', 'unknown')}"
            )
        
        # Check file size (10MB = 10 * 1024 * 1024 bytes)
        max_size = 10 * 1024 * 1024
        file_size = attachment_info.get('size', 0)
        
        if file_size > max_size:
            size_mb = file_size / (1024 * 1024)
            raise PDFValidationError(
                f"File too large. Maximum size is 10MB, got {size_mb:.1f}MB"
            )
        
        if file_size == 0:
            raise PDFValidationError("File appears to be empty")
        
        # Download the file
        download_url = attachment_info.get('url')
        if not download_url:
            raise PDFValidationError("No download URL provided")
        
        print(f"Downloading PDF from: {download_url}")
        
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        file_bytes = response.content
        
        # Validate it's actually a PDF by trying to read it
        try:
            pdf_stream = BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            # Try to get the number of pages (this will fail if it's not a valid PDF)
            page_count = len(pdf_reader.pages)
            
            if page_count == 0:
                raise PDFValidationError("PDF appears to have no pages")

            print(f"Successfully validated PDF: {page_count} pages, {len(file_bytes)} bytes")
            
        except Exception as e:
            raise PDFValidationError(f"Invalid PDF file: {str(e)}")
        
        return file_bytes
        
    except requests.RequestException as e:
        raise PDFValidationError(f"Failed to download file: {str(e)}")
    except ValueError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise PDFValidationError(f"Unexpected error during validation: {str(e)}")


