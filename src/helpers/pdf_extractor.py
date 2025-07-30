import os
import logging
import requests
import io
from PyPDF2 import PdfReader
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf_url(pdf_url: str) -> Optional[str]:
    """
    Extract text content from a PDF at the given URL
    
    Args:
        pdf_url (str): URL of the PDF to extract text from
        
    Returns:
        str or None: Extracted text content or None if failed
    """
    try:
        # Download PDF content
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Create PDF reader from bytes
        pdf_buffer = io.BytesIO(response.content)
        pdf_reader = PdfReader(pdf_buffer)
        
        # Extract text from all pages
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        if not text_content.strip():
            logger.warning(f"No text content extracted from PDF: {pdf_url}")
            return None
            
        logger.info(f"Successfully extracted {len(text_content)} characters from PDF")
        return text_content.strip()
        
    except requests.RequestException as e:
        logger.error(f"Error downloading PDF from {pdf_url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None


def clean_resume_text(text: str) -> str:
    """
    Clean and format resume text for AI analysis
    
    Args:
        text (str): Raw text extracted from PDF
        
    Returns:
        str: Cleaned text ready for AI processing
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    cleaned_text = '\n'.join(lines)
    
    # Remove excessive newlines
    while '\n\n\n' in cleaned_text:
        cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
    
    return cleaned_text


def validate_resume_content(text: str) -> bool:
    """
    Validate that the extracted text looks like a resume
    
    Args:
        text (str): Extracted text content
        
    Returns:
        bool: True if content appears to be a resume
    """
    if not text or len(text) < 100:
        return False
    
    # Look for common resume keywords
    resume_indicators = [
        'experience', 'education', 'skills', 'work', 'employment',
        'university', 'college', 'degree', 'resume', 'cv',
        'email', 'phone', 'contact', 'objective', 'summary'
    ]
    
    text_lower = text.lower()
    found_indicators = sum(1 for indicator in resume_indicators if indicator in text_lower)
    
    # If we find at least 3 resume indicators, consider it a resume
    return found_indicators >= 3