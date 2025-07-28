import requests
import PyPDF2
from io import BytesIO


class PDFValidationError(Exception):
    """Custom exception for PDF validation errors"""
    pass


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
    except PDFValidationError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        raise PDFValidationError(f"Unexpected error during validation: {str(e)}")


def get_pdf_info(file_bytes):
    """
    Extract basic information from a PDF file
    
    Args:
        file_bytes (bytes): PDF file content
        
    Returns:
        dict: PDF information including page count, title, etc.
    """
    try:
        pdf_stream = BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        
        info = {
            'page_count': len(pdf_reader.pages),
            'encrypted': pdf_reader.is_encrypted,
        }
        
        # Try to get metadata
        if pdf_reader.metadata:
            info['title'] = pdf_reader.metadata.get('/Title', '')
            info['author'] = pdf_reader.metadata.get('/Author', '')
            info['creator'] = pdf_reader.metadata.get('/Creator', '')
        
        return info
        
    except Exception as e:
        print(f"Error extracting PDF info: {e}")
        return {'page_count': 0, 'encrypted': False}