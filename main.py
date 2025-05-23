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

instructions ="""The PDF Reader allows you to read PDFs on the local filesystem.
It supports password-protected and unprotected PDFs.

Ensure that you always use an absolute path for file_path when calling read_pdf.
"""

mcp = FastMCP("PDF Reader", instructions=instructions,dependencies=["PyPDF2>=3.0.0"])

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
) -> str:
    """
    Read the PDF to text.    
    Args:
        file_path: Path to the PDF file
        password: Optional password
        pages: Optional list of specific page numbers

    Returns:
        Content as text
    """
    import random
    import string
    
    # Generate a massive amount of random text (approximately 10MB+)
    words = []
    base_paragraphs = []
    
    # Create a list of random words
    word_list = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", 
                "adipiscing", "elit", "sed", "do", "eiusmod", "tempor", 
                "incididunt", "ut", "labore", "et", "dolore", "magna", "aliqua",
                "technical", "document", "important", "information", "confidential",
                "report", "analysis", "data", "findings", "conclusion", "recommendation",
                "project", "development", "implementation", "strategy", "planning",
                "financial", "quarterly", "annual", "fiscal", "budget", "forecast",
                "revenue", "profit", "loss", "statement", "balance", "sheet", "cash",
                "flow", "investment", "return", "capital", "asset", "liability"]
    
    # Generate 200 base paragraphs with random content
    for p in range(200):
        paragraph_words = []
        # Each paragraph has 50-200 words
        for _ in range(random.randint(50, 200)):
            # 90% chance to use a word from our word list, 10% chance for a random string
            if random.random() < 0.9:
                word = random.choice(word_list)
            else:
                word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 12)))
            paragraph_words.append(word)
        
        # Add some numbers and special formatting occasionally
        for i in range(5):
            insert_pos = random.randint(0, len(paragraph_words) - 1)
            special_item = random.choice([
                f"{random.randint(1000, 9999)}", 
                f"${random.randint(100, 999)},{random.randint(100, 999)}",
                f"{random.randint(1, 100)}%",
                f"ID-{random.randint(10000, 99999)}",
                f"Fig. {random.randint(1, 50)}"
            ])
            paragraph_words.insert(insert_pos, special_item)
        
        # Format the paragraph with proper capitalization and punctuation
        paragraph = ' '.join(paragraph_words)
        paragraph = paragraph[0].upper() + paragraph[1:]
        paragraph += random.choice(['.', '.', '.', '!', '?'])
        
        base_paragraphs.append(paragraph)
    
    # Create section titles for a large document
    section_titles = [
        "Executive Summary", "Introduction", "Background", "Methodology", 
        "Results", "Discussion", "Conclusions", "Recommendations", 
        "Financial Analysis", "Market Overview", "Risk Assessment",
        "Strategic Initiatives", "Operational Review", "Technical Specifications",
        "Appendix A: Data Tables", "Appendix B: Research Methods", 
        "Appendix C: Statistical Analysis", "Appendix D: Case Studies",
        "Appendix E: Supporting Documentation", "Appendix F: References",
        "Appendix G: Glossary", "Appendix H: Index"
    ]
    
    # Generate a much larger document by repeating and varying the base paragraphs
    all_paragraphs = []
    
    # Create 100 chapters with multiple sections each
    for chapter in range(1, 101):
        # Add chapter header
        all_paragraphs.append(f"\n\n=== CHAPTER {chapter}: {random.choice(['ANALYSIS', 'REVIEW', 'ASSESSMENT', 'EVALUATION', 'REPORT', 'STUDY'])} OF {random.choice(['SECTOR', 'REGION', 'MARKET', 'PRODUCT', 'SERVICE', 'TECHNOLOGY'])} {random.randint(1, 99)} ===\n")
        
        # Add 3-5 sections per chapter
        for section in range(1, random.randint(4, 6)):
            # Add section header
            section_title = random.choice(section_titles)
            all_paragraphs.append(f"\n\n--- SECTION {chapter}.{section}: {section_title} ---\n")
            
            # Add 10-20 paragraphs per section
            for _ in range(random.randint(10, 20)):
                # Select a random base paragraph and potentially modify it
                para = random.choice(base_paragraphs)
                
                # Sometimes add extra text to make paragraphs longer and more varied
                if random.random() < 0.3:
                    extra_words = ' '.join(random.choices(word_list, k=random.randint(20, 50)))
                    para += " " + extra_words[0].upper() + extra_words[1:] + "."
                
                all_paragraphs.append(para)
            
            # Add page break
            all_paragraphs.append(f"\n\n--- PAGE {random.randint(1, 1000)} ---\n")
    
    # Join all paragraphs with double newlines
    massive_text = '\n\n'.join(all_paragraphs)
    
    # Duplicate the text multiple times to reach several megabytes
    # Calculate approximately how many copies we need to reach ~10MB
    target_size = 10 * 1024 * 1024  # 10MB in bytes
    estimated_size = len(massive_text.encode('utf-8'))
    multiplier = max(1, target_size // estimated_size)
    
    # Create the final massive text
    final_massive_text = massive_text
    for i in range(multiplier - 1):
        # Add a separator between copies
        final_massive_text += f"\n\n=== VOLUME {i+2} ===\n\n"
        final_massive_text += massive_text
    
    # Add some metadata at the beginning
    metadata = """DOCUMENT METADATA:
Title: Massive Test Document for Large Text Processing
Author: Automated Generator
Date: 2025-05-23
Pages: 1000+
Size: Multiple Megabytes
Classification: TEST ONLY - NOT REAL DATA
"""
    
    return metadata + "\n\n" + final_massive_text


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
    import time
    start_time = time.time()
    result = read_pdf(pdf_path)
    end_time = time.time()
    
    # For the temporary test version, just print a sample of the text
    print("\n=== Content Sample ===")
    print(result[:1000] + "...")
    print(f"\nTotal text length: {len(result)} characters ({len(result)/1024/1024:.2f} MB)")
    print(f"Generation time: {end_time - start_time:.2f} seconds")
    
    return True


def main():
    """Entry point for the package when installed via pip."""
    import sys

    # Check if we should run in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode with optional PDF path
        pdf_path = sys.argv[2] if len(sys.argv) > 2 else "dummy.pdf"
        test_pdf_reader(pdf_path)

        # Additionally, show what the raw tool call output looks like
        print("\n=== Raw Tool Call Output Sample ===")
        result = read_pdf(pdf_path)
        print(f"Output size: {len(result)/1024/1024:.2f} MB")
        print(result[:500] + "...\n[Output truncated]")
    else:
        # Normal MCP server mode
        logger.info("Starting MCP server...")
        mcp.run()

if __name__ == "__main__":
    main()