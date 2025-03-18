from mcp.server.fastmcp import FastMCP
import os
import PyPDF2
from typing import Dict, List, Optional, Any
import logging
import tempfile
import uuid
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("Starting PDF Reader MCP server...")

mcp = FastMCP("PDF Reader", dependencies=["PyPDF2>=3.0.0"])

# Create a temporary directory for storing extracted page content
TEMP_DIR = os.path.join(tempfile.gettempdir(), "pdf_reader_extracts")
os.makedirs(TEMP_DIR, exist_ok=True)
logger.info(f"Using temporary directory for PDF extracts: {TEMP_DIR}")

def cleanup_old_files(max_age_hours=24):
    """
    Clean up old temporary files that might have been left behind
    
    Args:
        max_age_hours: Maximum age of files to keep in hours
    """
    import time
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    try:
        for file_path in Path(TEMP_DIR).glob("*.txt"):
            if current_time - file_path.stat().st_mtime > max_age_seconds:
                logger.info(f"Cleaning up old file: {file_path}")
                file_path.unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")

# Clean up old files on startup
cleanup_old_files()

#
# PDF Reader functionality
#


@mcp.tool()
def read_pdf(
    file_path: str, password: str = None, pages: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Read a PDF file and extract its text. Works with both protected and unprotected PDFs.
    Instead of returning the text directly, writes each page to a temporary file and returns the file paths.

    Args:
        file_path: Path to the PDF file
        password: Optional password to decrypt the PDF if it's protected
        pages: Optional list of specific page numbers to extract (1-indexed). If None, all pages are extracted.

    Returns:
        Dictionary containing paths to extracted page content files and metadata
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    try:
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)

            # Check if PDF is encrypted
            is_encrypted = pdf_reader.is_encrypted

            # Try to decrypt if necessary
            decrypt_success = True
            if is_encrypted:
                if password is None:
                    return {
                        "success": False,
                        "error": "This PDF is password-protected. Please provide a password.",
                        "is_encrypted": True,
                        "password_required": True,
                    }
                decrypt_success = pdf_reader.decrypt(password)

            # Return error if decryption failed
            if is_encrypted and not decrypt_success:
                return {
                    "success": False,
                    "error": "Incorrect password or PDF could not be decrypted",
                    "is_encrypted": True,
                    "password_required": True,
                }

            # Extract metadata
            metadata = {}
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    if key.startswith("/"):
                        metadata[key[1:]] = value
                    else:
                        metadata[key] = value

            # Determine which pages to extract
            total_pages = len(pdf_reader.pages)
            pages_to_extract = pages or list(range(1, total_pages + 1))

            # Convert to 0-indexed for internal use
            zero_indexed_pages = [
                p - 1 for p in pages_to_extract if 1 <= p <= total_pages
            ]

            # Generate a unique ID for this extraction session
            session_id = str(uuid.uuid4())[:8]
            pdf_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Create a metadata file with information about the PDF
            metadata_file_path = os.path.join(TEMP_DIR, f"{pdf_name}_{session_id}_metadata.json")
            with open(metadata_file_path, 'w') as meta_file:
                json.dump({
                    "filename": os.path.basename(file_path),
                    "total_pages": total_pages,
                    "is_encrypted": is_encrypted,
                    "metadata": metadata,
                    "session_id": session_id,
                    "extracted_pages": [p + 1 for p in zero_indexed_pages]
                }, meta_file, indent=2)

            # Extract content from requested pages and write to temp files
            content_files = {}
            for page_number in zero_indexed_pages:
                page = pdf_reader.pages[page_number]
                text = page.extract_text()
                
                # Create a temporary file for this page
                page_file_path = os.path.join(
                    TEMP_DIR, f"{pdf_name}_{session_id}_page_{page_number + 1}.txt"
                )
                
                # Write the content to the file
                with open(page_file_path, 'w', encoding='utf-8') as page_file:
                    page_file.write(text)
                
                # Store the file path
                content_files[page_number + 1] = page_file_path

            return {
                "success": True,
                "is_encrypted": is_encrypted,
                "total_pages": total_pages,
                "extracted_pages": list(content_files.keys()),
                "metadata": metadata,
                "metadata_file": metadata_file_path,
                "content_files": content_files,
                "session_id": session_id,
                "temp_dir": TEMP_DIR
            }

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return {"success": False, "error": f"Error processing PDF: {str(e)}"}


def test_pdf_reader(pdf_path="visa-rules-public.pdf"):
    """
    Test the PDF reader functionality with a specific PDF file.

    Args:
        pdf_path: Path to the PDF file to test
    """
    logger.info(f"Testing PDF reader with {pdf_path}")

    # Test if file exists
    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        return False

    # Test reading the PDF
    logger.info(f"Reading PDF file: {pdf_path}")
    result = read_pdf(pdf_path)

    # Print results
    if result["success"]:
        logger.info(f"Successfully read PDF with {result['total_pages']} pages")

        # Print metadata in a more readable format
        print("\n=== PDF Metadata ===")
        for key, value in result["metadata"].items():
            print(f"{key}: {value}")
        
        # Print information about the temp files
        print(f"\n=== Temporary Files ===")
        print(f"Metadata file: {result['metadata_file']}")
        print(f"Session ID: {result['session_id']}")
        print(f"Temporary directory: {result['temp_dir']}")
        print(f"Number of content files: {len(result['content_files'])}")
        
        # Print a sample of the content files
        print("\n=== Content Files ===")
        for page_num, file_path in sorted(result['content_files'].items())[:3]:
            print(f"Page {page_num}: {file_path}")
            
        # Read and display content from the first page file
        first_page = min(result['content_files'].keys())
        first_page_path = result['content_files'][first_page]
        print(f"\n=== Content Sample (Page {first_page}) ===")
        try:
            with open(first_page_path, 'r', encoding='utf-8') as f:
                content = f.read()
                content_sample = content[:500] + "..." if len(content) > 500 else content
                print(f"{content_sample}")
        except Exception as e:
            print(f"Error reading file: {e}")

        # Read a few random page files
        import random
        sample_pages = random.sample(
            list(result['content_files'].keys()), 
            min(3, len(result['content_files']))
        )
        for page in sample_pages:
            if page != first_page:  # Skip first page as we've already shown it
                page_path = result['content_files'][page]
                print(f"\n=== Content Sample (Page {page}) ===")
                try:
                    with open(page_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        content_sample = content[:300] + "..." if len(content) > 300 else content
                        print(f"{content_sample}")
                except Exception as e:
                    print(f"Error reading file: {e}")

        print(f"\nTotal pages: {result['total_pages']}")
        print(f"Is encrypted: {result['is_encrypted']}")
        return True
    else:
        logger.error(f"Failed to read PDF: {result['error']}")
        return False


if __name__ == "__main__":
    import sys
    
    # Check if we should run in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode with optional PDF path
        pdf_path = sys.argv[2] if len(sys.argv) > 2 else "visa-rules-public.pdf"
        test_pdf_reader(pdf_path)
    else:
        # Normal MCP server mode
        logger.info("Starting MCP server...")
        mcp.run()

@mcp.prompt()
def pdf_reader_prompt(file_path: str = "") -> str:
    """
    Create a prompt for reading and summarizing a PDF file.
    
    Args:
        file_path: Path to the PDF file
    """
    if file_path:
        return f"""I have a PDF file at "{file_path}" that I'd like to read and analyze.

Please use the PDF Reader tool to extract and summarize the content of this document for me.
If the PDF is password-protected, I'll provide the password when asked.

The content will be extracted to temporary files that you can access.
"""
    else:
        return """I'd like to read and analyze a PDF file.

I'll provide the file path, and then I'd like you to use the PDF Reader tool to extract and summarize the document for me.
If the PDF is password-protected, I'll provide the password when asked.

The content will be extracted to temporary files that you can access.
"""
