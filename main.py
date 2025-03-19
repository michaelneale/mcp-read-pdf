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
    Use this anytime you need to read a PDF file and extract its text.
    Works with both protected and unprotected PDFs, complex and large PDFs.
    Instead of returning the text directly, writes content to a single temporary file and returns the file path.
    This will work with very large and complex PDFs

    Args:
        file_path: Path to the PDF file
        password: Optional password to decrypt the PDF if it's protected
        pages: Optional list of specific page numbers to extract (1-indexed). If None, all pages are extracted.

    Returns:
        json containing path to extracted text content file and metadata
        The file returned may be large so use tools like ripgrep to search it
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    try:
        # Get the file size
        file_size = os.path.getsize(file_path)

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
                        "file_size": file_size,
                    }
                decrypt_success = pdf_reader.decrypt(password)

            # Return error if decryption failed
            if is_encrypted and not decrypt_success:
                return {
                    "success": False,
                    "error": "Incorrect password or PDF could not be decrypted",
                    "is_encrypted": True,
                    "password_required": True,
                    "file_size": file_size,
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

            # Create a single content file
            content_file_path = os.path.join(
                TEMP_DIR, f"{pdf_name}_{session_id}_content.txt"
            )

            # Extract content from requested pages and write to a single file
            with open(content_file_path, "w", encoding="utf-8") as content_file:
                for page_number in zero_indexed_pages:
                    page = pdf_reader.pages[page_number]
                    text = page.extract_text()

                    # Write page header and content
                    content_file.write(f"--- PAGE {page_number + 1} ---\n")
                    content_file.write(text)
                    content_file.write("\n\n")

            # Get the content file size
            content_file_size = os.path.getsize(content_file_path)

            return {
                "success": True,
                "is_encrypted": is_encrypted,
                "total_pages": total_pages,
                "metadata": metadata,
                "content_file": content_file_path,
                "session_id": session_id,
                "temp_dir": TEMP_DIR,
                "file_size": file_size,
                "content_file_size": content_file_size,
            }

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return {
            "success": False,
            "error": f"Error processing PDF: {str(e)}",
            "file_size": file_size if "file_size" in locals() else None,
        }


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
        print(f"Session ID: {result['session_id']}")
        print(f"Temporary directory: {result['temp_dir']}")
        print(f"Content file: {result['content_file']}")
        print(f"Original file size: {result['file_size']} bytes")
        print(f"Content file size: {result['content_file_size']} bytes")

        # Read and display content from the content file
        print(f"\n=== Content Sample ===")
        try:
            with open(result["content_file"], "r", encoding="utf-8") as f:
                content = f.read(1000)  # Read first 1000 characters
                print(f"{content}...")
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
        pdf_path = sys.argv[2] if len(sys.argv) > 2 else "dummy.pdf"
        test_pdf_reader(pdf_path)

        # Additionally, show what the raw tool call output looks like
        print("\n=== Raw Tool Call Output ===")
        result = read_pdf(pdf_path)
        import json

        print(json.dumps(result, indent=2))
    else:
        # Normal MCP server mode
        logger.info("Starting MCP server...")
        mcp.run()
