"""Data validation utilities using Pydantic for SSV-Book-Generator.

This module provides:
- Pydantic models for data validation
- Enums for book types, formats, and providers
- Custom validators for files and paths
- Type hints for all data structures
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, validator, field_validator
import os


# Enums
class BookFormat(str, Enum):
    """Supported book output formats."""
    PDF = "pdf"
    EPUB = "epub"
    HTML = "html"
    DOCX = "docx"


class ContentType(str, Enum):
    """Types of book content."""
    SCIENTIFIC = "scientific"
    FICTION = "fiction"
    SURGERY = "surgery"
    ONCOLOGY = "oncology"
    EDUCATIONAL = "educational"
    REVIEW = "review"
    NARRATIVE = "narrative"
    TEXTBOOK = "textbook"


class APIProvider(str, Enum):
    """Supported AI API providers."""
    OPENAI_GPT = "openai_gpt"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    OPENAI_DALLE = "openai_dalle"
    STABLE_DIFFUSION = "stable_diffusion"
    PLACEHOLDER = "placeholder"


class TargetAudience(str, Enum):
    """Target audience types."""
    DOCTORS = "doctors"
    STUDENTS = "students"
    PATIENTS = "patients"
    GENERAL_PUBLIC = "general_public"
    RESEARCHERS = "researchers"


# Pydantic Models
class BookMetadata(BaseModel):
    """Metadata for the generated book."""
    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author: str = Field(default="SSVproff", description="Author name")
    language: str = Field(default="ru", description="Book language code")
    book_type: ContentType = Field(default=ContentType.SCIENTIFIC, description="Type of content")
    target_audience: TargetAudience = Field(default=TargetAudience.STUDENTS, description="Target audience")
    genre: str = Field(default="educational", description="Book genre")
    description: Optional[str] = Field(None, max_length=2000, description="Book description")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Book keywords")
    
    class Config:
        use_enum_values = True


class ChapterData(BaseModel):
    """Data for a single chapter."""
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    title: str = Field(..., min_length=1, max_length=300, description="Chapter title")
    content: str = Field(..., min_length=1, description="Chapter content")
    summary: Optional[str] = Field(None, max_length=1000, description="Chapter summary")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Chapter keywords")
    
    @field_validator('content')
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Ensure content is not too short."""
        if len(v.strip()) < 100:
            raise ValueError("Chapter content must be at least 100 characters")
        return v


class AIConfig(BaseModel):
    """Configuration for AI providers."""
    content_provider: APIProvider = Field(default=APIProvider.OPENAI_GPT, description="Content generation provider")
    content_model: str = Field(default="gpt-4o", description="Content generation model")
    image_provider: APIProvider = Field(default=APIProvider.PLACEHOLDER, description="Image generation provider")
    image_model: str = Field(default="dall-e-3", description="Image generation model")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="AI temperature")
    max_tokens: Optional[int] = Field(None, ge=100, le=32000, description="Maximum tokens per request")
    
    class Config:
        use_enum_values = True


class FormattingConfig(BaseModel):
    """Configuration for book formatting."""
    output_format: BookFormat = Field(default=BookFormat.PDF, description="Output format")
    template: str = Field(default="academic", description="Template name")
    font_size: int = Field(default=12, ge=8, le=24, description="Font size")
    line_spacing: float = Field(default=1.5, ge=1.0, le=3.0, description="Line spacing")
    page_numbers: bool = Field(default=True, description="Include page numbers")
    table_of_contents: bool = Field(default=True, description="Generate table of contents")
    
    class Config:
        use_enum_values = True


class OpenScienceConfig(BaseModel):
    """Configuration for Open Science artifacts."""
    generate_artifacts: bool = Field(default=True, description="Save generation artifacts")
    generate_readme: bool = Field(default=True, description="Create README in package")
    include_metadata: bool = Field(default=True, description="Include metadata files")
    save_prompts: bool = Field(default=True, description="Save AI prompts used")


class BookContentRequest(BaseModel):
    """Complete request for book generation."""
    input_file: Path = Field(..., description="Path to input transcript/ideas file")
    output_dir: Path = Field(default=Path("./output"), description="Output directory")
    metadata: BookMetadata = Field(default_factory=BookMetadata, description="Book metadata")
    ai_config: AIConfig = Field(default_factory=AIConfig, description="AI configuration")
    formatting: FormattingConfig = Field(default_factory=FormattingConfig, description="Formatting configuration")
    open_science: OpenScienceConfig = Field(default_factory=OpenScienceConfig, description="Open Science configuration")
    
    @field_validator('input_file')
    @classmethod
    def validate_input_file(cls, v: Path) -> Path:
        """Ensure input file exists and is readable."""
        if not v.exists():
            raise ValueError(f"Input file does not exist: {v}")
        if not v.is_file():
            raise ValueError(f"Input path is not a file: {v}")
        if not os.access(v, os.R_OK):
            raise ValueError(f"Input file is not readable: {v}")
        return v
    
    @field_validator('output_dir')
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Ensure output directory is valid."""
        if v.exists() and not v.is_dir():
            raise ValueError(f"Output path exists but is not a directory: {v}")
        return v
    
    class Config:
        arbitrary_types_allowed = True


class ImageGenerationRequest(BaseModel):
    """Request for image generation."""
    prompt: str = Field(..., min_length=10, max_length=2000, description="Image generation prompt")
    style: Optional[str] = Field(None, description="Image style")
    size: str = Field(default="1024x1024", description="Image size")
    provider: APIProvider = Field(default=APIProvider.PLACEHOLDER, description="Image provider")
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v: str) -> str:
        """Validate image size format."""
        valid_sizes = ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]
        if v not in valid_sizes:
            raise ValueError(f"Invalid size. Must be one of: {', '.join(valid_sizes)}")
        return v
    
    class Config:
        use_enum_values = True


# Utility functions
def validate_file_path(path: str) -> Path:
    """Validate and convert string path to Path object.
    
    Args:
        path: String path to validate
    
    Returns:
        Path object
    
    Raises:
        ValueError: If path is invalid
    """
    try:
        p = Path(path)
        if p.exists() and not p.is_file():
            raise ValueError(f"Path exists but is not a file: {path}")
        return p
    except Exception as e:
        raise ValueError(f"Invalid file path: {path}") from e


def validate_directory_path(path: str, create_if_missing: bool = False) -> Path:
    """Validate and optionally create directory path.
    
    Args:
        path: String path to validate
        create_if_missing: Create directory if it doesn't exist
    
    Returns:
        Path object
    
    Raises:
        ValueError: If path is invalid
    """
    try:
        p = Path(path)
        if create_if_missing and not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        elif p.exists() and not p.is_dir():
            raise ValueError(f"Path exists but is not a directory: {path}")
        return p
    except Exception as e:
        raise ValueError(f"Invalid directory path: {path}") from e
