from mcp.server.fastmcp import FastMCP
import os
import PyPDF2
from typing import Dict, List, Optional

mcp = FastMCP(
    "PDF Reader", 
    dependencies=["PyPDF2>=3.0.0"]
)

#
# PDF Reader functionality
#

@mcp.tool()
def read_pdf(
    file_path: str,
    password: str = None,
    pages: Optional[List[int]] = None
) -> Dict:
    """
    Read a PDF file and extract its text. Works with both protected and unprotected PDFs.
    
    Args:
        file_path: Path to the PDF file
        password: Optional password to decrypt the PDF if it's protected
        pages: Optional list of specific page numbers to extract (1-indexed). If None, all pages are extracted.
        
    Returns:
        Dictionary containing the PDF content by page and metadata
    """
    # Check if file exists
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }
    
    try:
        with open(file_path, 'rb') as file:
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
                        "password_required": True
                    }
                decrypt_success = pdf_reader.decrypt(password)
            
            # Return error if decryption failed
            if is_encrypted and not decrypt_success:
                return {
                    "success": False,
                    "error": "Incorrect password or PDF could not be decrypted",
                    "is_encrypted": True,
                    "password_required": True
                }
            
            # Extract metadata
            metadata = {}
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    if key.startswith('/'):
                        metadata[key[1:]] = value
                    else:
                        metadata[key] = value
            
            # Determine which pages to extract
            total_pages = len(pdf_reader.pages)
            pages_to_extract = pages or list(range(1, total_pages + 1))
            
            # Convert to 0-indexed for internal use
            zero_indexed_pages = [p - 1 for p in pages_to_extract if 1 <= p <= total_pages]
            
            # Extract content from requested pages
            content = {}
            for page_number in zero_indexed_pages:
                page = pdf_reader.pages[page_number]
                content[page_number + 1] = page.extract_text()
            
            return {
                "success": True,
                "is_encrypted": is_encrypted,
                "total_pages": total_pages,
                "extracted_pages": list(content.keys()),
                "metadata": metadata,
                "content": content
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing PDF: {str(e)}"
        }

@mcp.resource("pdf://{file_path}")
def pdf_resource_no_password(file_path: str) -> str:
    """
    Read a PDF file and format its content as a resource.
    For unprotected PDFs.
    
    Args:
        file_path: Path to the PDF file
    """
    # Replace URL-encoded characters in file path
    file_path = file_path.replace('%20', ' ')
    
    result = read_pdf(file_path)
    
    if not result["success"]:
        if result.get("password_required", False):
            return f"# Password Required\n\nThis PDF is protected with a password. Please use the PDF resource with a password parameter: `pdf://{file_path}/YOUR_PASSWORD`"
        return f"# Error Reading PDF\n\n{result['error']}"
    
    # Format the PDF content as a Markdown document
    output = f"# PDF Content: {os.path.basename(file_path)}\n\n"
    
    if result["metadata"]:
        output += "## Metadata\n\n"
        for key, value in result["metadata"].items():
            output += f"- **{key}**: {value}\n"
        output += "\n"
    
    output += f"## Content ({result['total_pages']} pages total)\n\n"
    
    for page_num, page_text in result["content"].items():
        output += f"### Page {page_num}\n\n"
        output += page_text + "\n\n"
    
    return output

@mcp.resource("pdf://{file_path}/{password}")
def pdf_resource_with_password(file_path: str, password: str) -> str:
    """
    Read a password-protected PDF file and format its content as a resource.
    
    Args:
        file_path: Path to the PDF file
        password: Password to decrypt the PDF
    """
    # Replace URL-encoded characters in file path
    file_path = file_path.replace('%20', ' ')
    
    result = read_pdf(file_path, password)
    
    if not result["success"]:
        return f"# Error Reading PDF\n\n{result['error']}"
    
    # Format the PDF content as a Markdown document
    output = f"# PDF Content: {os.path.basename(file_path)}\n\n"
    
    if result["metadata"]:
        output += "## Metadata\n\n"
        for key, value in result["metadata"].items():
            output += f"- **{key}**: {value}\n"
        output += "\n"
    
    output += f"## Content ({result['total_pages']} pages total)\n\n"
    
    for page_num, page_text in result["content"].items():
        output += f"### Page {page_num}\n\n"
        output += page_text + "\n\n"
    
    return output

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
"""
    else:
        return """I'd like to read and analyze a PDF file.

I'll provide the file path, and then I'd like you to use the PDF Reader tool to extract and summarize the document for me.
If the PDF is password-protected, I'll provide the password when asked.
"""