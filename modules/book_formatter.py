"""
Enhanced book formatter with improved error handling and validation.

This module formats book content into various output formats (PDF, EPUB, HTML)
with integrated error handling, logging, and data validation using utils modules.

Features:
- Multiple format support (PDF, EPUB, HTML)
- Error handling with automatic retries
- Structured logging
- Data validation using Pydantic
- Custom styling and templates
- Image optimization
- Table of contents generation
"""

import logging
import os
import yaml
import uuid
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import utils modules
from utils.error_handler import (
    retry_on_error,
    handle_api_errors,
    safe_execute,
    ValidationError,
    FileProcessingError
)
from utils.logger import setup_logger, log_function_call
from utils.validator import (
    BookMetadata,
    ChapterData,
    BookConfig,
    validate_file_path,
    validate_chapters
)

# Setup logger
logger = setup_logger(__name__)

# Optional imports with fallback
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    logger.warning("FPDF2 library not available. Install with: pip install fpdf2")

try:
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False
    logger.warning("Ebooklib not available. Install with: pip install ebooklib")


class BookFormatterV2:
    """
    Enhanced book formatter with error handling and validation.
    
    Formats book content into multiple output formats with robust
    error handling, logging, and data validation.
    """
    
    @log_function_call()
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize formatter with optional configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        logger.info(f"BookFormatterV2 initialized with config: {self.config}")
    
    @retry_on_error(max_attempts=3)
    def _load_config(self, config_path: Optional[str]) -> BookConfig:
        """
        Load and validate configuration.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Validated BookConfig object
        """
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            return BookConfig(**config_data)
        else:
            # Return default config
            return BookConfig(
                title="Untitled Book",
                author="Unknown Author"
            )
    
    @log_function_call()
    @handle_api_errors
    def format_to_pdf(self,
                     metadata: BookMetadata,
                     chapters: List[ChapterData],
                     output_path: str) -> str:
        """
        Format book to PDF with error handling.
        
        Args:
            metadata: Book metadata
            chapters: List of chapter data
            output_path: Output file path
            
        Returns:
            Path to generated PDF file
            
        Raises:
            FileProcessingError: If PDF generation fails
            ValidationError: If data validation fails
        """
        if not FPDF_AVAILABLE:
            raise FileProcessingError(
                "FPDF2 not available. Install with: pip install fpdf2"
            )
        
        # Validate inputs
        validate_file_path(output_path, must_exist=False)
        validate_chapters(chapters)
        
        logger.info(f"Generating PDF: {output_path}")
        
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Add title page
            pdf.add_page()
            pdf.set_font('Arial', 'B', 24)
            pdf.cell(0, 10, metadata.title, ln=True, align='C')
            pdf.set_font('Arial', 'I', 14)
            pdf.cell(0, 10, f"by {metadata.author}", ln=True, align='C')
            
            # Add chapters
            for chapter in chapters:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, chapter.title, ln=True)
                pdf.ln(5)
                
                pdf.set_font('Arial', '', 12)
                # Handle unicode properly
                try:
                    pdf.multi_cell(0, 5, chapter.content)
                except Exception as e:
                    logger.warning(f"Unicode error in chapter {chapter.chapter_num}: {e}")
                    # Fallback: encode/decode
                    safe_content = chapter.content.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 5, safe_content)
            
            # Save PDF
            pdf.output(output_path)
            logger.info(f"PDF generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise FileProcessingError(f"Failed to generate PDF: {e}")
    
    @log_function_call()
    @handle_api_errors
    def format_to_epub(self,
                      metadata: BookMetadata,
                      chapters: List[ChapterData],
                      output_path: str) -> str:
        """
        Format book to EPUB with error handling.
        
        Args:
            metadata: Book metadata
            chapters: List of chapter data
            output_path: Output file path
            
        Returns:
            Path to generated EPUB file
            
        Raises:
            FileProcessingError: If EPUB generation fails
        """
        if not EPUB_AVAILABLE:
            raise FileProcessingError(
                "Ebooklib not available. Install with: pip install ebooklib"
            )
        
        # Validate inputs
        validate_file_path(output_path, must_exist=False)
        validate_chapters(chapters)
        
        logger.info(f"Generating EPUB: {output_path}")
        
        try:
            book = epub.EpubBook()
            
            # Set metadata
            book.set_identifier(str(uuid.uuid4()))
            book.set_title(metadata.title)
            book.set_language('en')
            book.add_author(metadata.author)
            
            # Add chapters
            epub_chapters = []
            for chapter in chapters:
                epub_chapter = epub.EpubHtml(
                    title=chapter.title,
                    file_name=f'chapter_{chapter.chapter_num}.xhtml',
                    lang='en'
                )
                epub_chapter.content = f'<h1>{chapter.title}</h1><p>{chapter.content}</p>'
                book.add_item(epub_chapter)
                epub_chapters.append(epub_chapter)
            
            # Add navigation
            book.toc = tuple(epub_chapters)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Add spine
            book.spine = ['nav'] + epub_chapters
            
            # Write EPUB file
            epub.write_epub(output_path, book, {})
            logger.info(f"EPUB generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"EPUB generation failed: {e}")
            raise FileProcessingError(f"Failed to generate EPUB: {e}")
    
    @log_function_call()
    @handle_api_errors
    def format_to_html(self,
                      metadata: BookMetadata,
                      chapters: List[ChapterData],
                      output_path: str,
                      template_path: Optional[str] = None) -> str:
        """
        Format book to HTML with error handling.
        
        Args:
            metadata: Book metadata
            chapters: List of chapter data
            output_path: Output file path
            template_path: Optional custom template path
            
        Returns:
            Path to generated HTML file
            
        Raises:
            FileProcessingError: If HTML generation fails
        """
        # Validate inputs
        validate_file_path(output_path, must_exist=False)
        validate_chapters(chapters)
        
        logger.info(f"Generating HTML: {output_path}")
        
        try:
            # Build HTML content
            html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        .chapter {{
            margin-bottom: 40px;
        }}
        .metadata {{
            text-align: center;
            margin-bottom: 50px;
        }}
        .author {{
            font-style: italic;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="metadata">
        <h1>{metadata.title}</h1>
        <p class="author">by {metadata.author}</p>
    </div>
'''
            
            # Add chapters
            for chapter in chapters:
                html_content += f'''    <div class="chapter">
        <h2>{chapter.title}</h2>
        <p>{chapter.content}</p>
    </div>
'''
            
            html_content += '</body>\n</html>'
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"HTML generation failed: {e}")
            raise FileProcessingError(f"Failed to generate HTML: {e}")
    
    @log_function_call()
    def format_book(self,
                   metadata: BookMetadata,
                   chapters: List[ChapterData],
                   output_format: str,
                   output_path: str) -> str:
        """
        Format book to specified format.
        
        Args:
            metadata: Book metadata
            chapters: List of chapter data
            output_format: Output format (pdf, epub, html)
            output_path: Output file path
            
        Returns:
            Path to generated file
            
        Raises:
            ValidationError: If format is unsupported
        """
        format_lower = output_format.lower()
        
        if format_lower == 'pdf':
            return self.format_to_pdf(metadata, chapters, output_path)
        elif format_lower == 'epub':
            return self.format_to_epub(metadata, chapters, output_path)
        elif format_lower == 'html':
            return self.format_to_html(metadata, chapters, output_path)
        else:
            raise ValidationError(f"Unsupported format: {output_format}")


@log_function_call()
def format_book(metadata: Dict[str, Any],
               chapters: List[Dict[str, Any]],
               output_format: str,
               output_path: str,
               config_path: Optional[str] = None) -> str:
    """
    Convenience function to format a book.
    
    Args:
        metadata: Book metadata dict
        chapters: List of chapter dicts
        output_format: Output format (pdf, epub, html)
        output_path: Output file path
        config_path: Optional config file path
        
    Returns:
        Path to generated file
    """
    # Convert to Pydantic models
    book_metadata = BookMetadata(**metadata)
    chapter_data = [ChapterData(**ch) for ch in chapters]
    
    # Create formatter and format
    formatter = BookFormatterV2(config_path)
    return formatter.format_book(book_metadata, chapter_data, output_format, output_path)


if __name__ == "__main__":
    # Example usage
    logger.info("BookFormatterV2 module loaded")
    
    # Test with sample data
    test_metadata = {
        "title": "Medical Procedures Guide",
        "author": "Dr. Smith",
        "language": "en"
    }
    
    test_chapters = [
        {
            "chapter_num": 1,
            "title": "Introduction",
            "content": "This is the introduction to medical procedures."
        },
        {
            "chapter_num": 2,
            "title": "Chapter 1: Basic Procedures",
            "content": "This chapter covers basic medical procedures."
        }
    ]
    
    # Format to HTML (most reliable)
    output = format_book(
        metadata=test_metadata,
        chapters=test_chapters,
        output_format="html",
        output_path="test_book.html"
    )
    
    logger.info(f"Test book generated: {output}")
