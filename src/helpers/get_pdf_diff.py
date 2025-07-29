import requests
import PyPDF2
from io import BytesIO
import difflib
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf_url(pdf_url):
    """
    Download PDF from URL and extract all text content
    
    Args:
        pdf_url (str): URL to download PDF from
        
    Returns:
        str: Extracted text content
        
    Raises:
        Exception: If download or text extraction fails
    """
    try:
        # Download PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Extract text using PyPDF2
        pdf_stream = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        return text_content.strip()
        
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {pdf_url}: {str(e)}")
        raise


def compare_text_diff(old_pdf_url, new_pdf_url):
    """
    Compare text content between two PDFs and return added/removed text
    
    Args:
        old_pdf_url (str): URL of the original PDF
        new_pdf_url (str): URL of the updated PDF
        
    Returns:
        dict: Dictionary with 'added_text' and 'removed_text' keys
        
    Raises:
        Exception: If PDF download or comparison fails
    """
    try:
        logger.info(f"Comparing PDFs: {old_pdf_url} vs {new_pdf_url}")
        
        # Extract text from both PDFs
        old_text = extract_text_from_pdf_url(old_pdf_url)
        new_text = extract_text_from_pdf_url(new_pdf_url)
        
        # Split into lines for better diff analysis
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        
        # Generate diff
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        
        added_lines = []
        removed_lines = []
        
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                # Remove the '+' prefix
                added_lines.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                # Remove the '-' prefix
                removed_lines.append(line[1:].strip())
        
        # Join lines and truncate if too long (Discord embed field limit is 1024 chars)
        added_text = '\n'.join(added_lines)
        removed_text = '\n'.join(removed_lines)
        
        # Truncate if too long for Discord embed
        max_length = 1000  # Leave some buffer for Discord formatting
        if len(added_text) > max_length:
            added_text = added_text[:max_length] + "...\n(truncated)"
        if len(removed_text) > max_length:
            removed_text = removed_text[:max_length] + "...\n(truncated)"
        
        # Filter out empty or whitespace-only changes
        if not added_text.strip():
            added_text = None
        if not removed_text.strip():
            removed_text = None
            
        logger.info(f"Diff comparison completed. Added: {len(added_text or '')} chars, Removed: {len(removed_text or '')} chars")
        
        return {
            'added_text': added_text,
            'removed_text': removed_text
        }
        
    except Exception as e:
        logger.error(f"Failed to compare PDF differences: {str(e)}")
        raise