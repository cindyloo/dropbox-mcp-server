#!/usr/bin/env python3
"""
Dropbox MCP Server for reading and querying files.
Supports PDF, DOCX, and text files with search capabilities.
HTTP transport version for Smithery deployment.
"""

import os
import io
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import dropbox
from dropbox.exceptions import AuthError, ApiError
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
import uvicorn
from starlette.middleware.cors import CORSMiddleware

# File processing libraries
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Dropbox File Reader")

# Global Dropbox client
dropbox_client: Optional[dropbox.Dropbox] = None


class FileInfo(BaseModel):
    """File information structure."""
    name: str
    path: str
    size: int
    modified: str
    is_folder: bool
    content_preview: Optional[str] = None


class SearchResult(BaseModel):
    """Search result structure."""
    file_path: str
    file_name: str
    match_context: str
    file_size: int
    modified: str


def initialize_dropbox_client():
    """Initialize Dropbox client with access token from environment."""
    global dropbox_client
    
    access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
    if not access_token:
        raise ValueError(
            "DROPBOX_ACCESS_TOKEN environment variable is required. "
            "Get your token from https://www.dropbox.com/developers/apps"
        )
    
    try:
        dropbox_client = dropbox.Dropbox(access_token)
        # Test the connection
        dropbox_client.users_get_current_account()
        logger.info("Dropbox client initialized successfully")
    except AuthError as e:
        raise ValueError(f"Invalid Dropbox access token: {e}")
    except Exception as e:
        raise ValueError(f"Failed to initialize Dropbox client: {e}")


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF content."""
    if not PyPDF2:
        return "[PDF text extraction not available - install PyPDF2]"
    
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"[Error extracting PDF text: {e}]"


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX content."""
    if not Document:
        return "[DOCX text extraction not available - install python-docx]"
    
    try:
        docx_file = io.BytesIO(file_content)
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"[Error extracting DOCX text: {e}]"


def get_file_content(file_path: str) -> str:
    """Download and extract text content from a Dropbox file."""
    if not dropbox_client:
        raise ValueError("Dropbox client not initialized")
    
    try:
        # Download file content
        _, response = dropbox_client.files_download(file_path)
        file_content = response.content
        
        # Extract text based on file extension
        file_ext = file_path.lower().split('.')[-1]
        
        if file_ext == 'pdf':
            return extract_text_from_pdf(file_content)
        elif file_ext in ['docx', 'doc']:
            return extract_text_from_docx(file_content)
        elif file_ext in ['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'csv']:
            # Text files
            try:
                return file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return file_content.decode('latin-1')
                except UnicodeDecodeError:
                    return "[Binary file - cannot display as text]"
        else:
            return f"[Unsupported file type: {file_ext}]"
            
    except ApiError as e:
        raise ValueError(f"Dropbox API error: {e}")
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")


@mcp.tool()
def search_files(query: str, file_types: str = "all", max_results: int = 10) -> List[SearchResult]:
    """
    Search for files in Dropbox by name or content.
    
    Args:
        query: Search query (searches file names and content)
        file_types: File types to search ("all", "pdf", "docx", "txt", or comma-separated list)
        max_results: Maximum number of results to return
    """
    if not dropbox_client:
        initialize_dropbox_client()
    
    results = []
    extensions = []
    
    # Parse file types
    if file_types.lower() == "all":
        extensions = ['.pdf', '.docx', '.doc', '.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.csv']
    elif file_types.lower() == "pdf":
        extensions = ['.pdf']
    elif file_types.lower() == "docx":
        extensions = ['.docx', '.doc']
    elif file_types.lower() == "txt":
        extensions = ['.txt', '.md']
    else:
        # Comma-separated list
        extensions = [f'.{ext.strip()}' for ext in file_types.split(',')]
    
    try:
        # Search by filename first
        search_result = dropbox_client.files_search_v2(
            query=query,
            options=dropbox.files.SearchOptions(
                max_results=max_results * 2  # Get more to filter by extension
            )
        )
        
        for match in search_result.matches:
            if len(results) >= max_results:
                break
                
            metadata = match.metadata.metadata
            if isinstance(metadata, dropbox.files.FileMetadata):
                file_path = metadata.path_lower
                file_name = metadata.name
                
                # Check if file extension matches
                if any(file_path.endswith(ext) for ext in extensions):
                    results.append(SearchResult(
                        file_path=file_path,
                        file_name=file_name,
                        match_context=f"Filename match: {file_name}",
                        file_size=metadata.size,
                        modified=metadata.server_modified.isoformat()
                    ))
        
        return results
        
    except Exception as e:
        raise ValueError(f"Search failed: {e}")


@mcp.tool()
def list_files(folder_path: str = "", max_files: int = 20) -> List[FileInfo]:
    """
    List files and folders in a Dropbox directory.
    
    Args:
        folder_path: Path to the folder (empty string for root)
        max_files: Maximum number of items to return
    """
    if not dropbox_client:
        initialize_dropbox_client()
    
    try:
        # Ensure path starts with / if not empty
        if folder_path and not folder_path.startswith('/'):
            folder_path = '/' + folder_path
        
        # List folder contents
        result = dropbox_client.files_list_folder(
            folder_path,
            limit=max_files
        )
        
        files = []
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                # Get preview for text files
                preview = None
                if entry.name.lower().endswith(('.txt', '.md', '.py', '.js')):
                    try:
                        content = get_file_content(entry.path_lower)
                        preview = content[:200] + "..." if len(content) > 200 else content
                    except:
                        preview = "[Could not load preview]"
                
                files.append(FileInfo(
                    name=entry.name,
                    path=entry.path_lower,
                    size=entry.size,
                    modified=entry.server_modified.isoformat(),
                    is_folder=False,
                    content_preview=preview
                ))
            elif isinstance(entry, dropbox.files.FolderMetadata):
                files.append(FileInfo(
                    name=entry.name,
                    path=entry.path_lower,
                    size=0,
                    modified="",
                    is_folder=True
                ))
        
        return files
        
    except Exception as e:
        raise ValueError(f"Failed to list files: {e}")


@mcp.tool()
def read_file(file_path: str, max_length: int = 5000) -> str:
    """
    Read and return the full content of a file.
    
    Args:
        file_path: Full path to the file in Dropbox
        max_length: Maximum characters to return (0 for no limit)
    """
    if not dropbox_client:
        initialize_dropbox_client()
    
    try:
        content = get_file_content(file_path)
        
        if max_length > 0 and len(content) > max_length:
            return content[:max_length] + f"\n\n[Content truncated - file has {len(content)} total characters]"
        
        return content
        
    except Exception as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")


@mcp.tool()
def get_file_info(file_path: str) -> FileInfo:
    """
    Get detailed information about a specific file.
    
    Args:
        file_path: Full path to the file in Dropbox
    """
    if not dropbox_client:
        initialize_dropbox_client()
    
    try:
        metadata = dropbox_client.files_get_metadata(file_path)
        
        if isinstance(metadata, dropbox.files.FileMetadata):
            return FileInfo(
                name=metadata.name,
                path=metadata.path_lower,
                size=metadata.size,
                modified=metadata.server_modified.isoformat(),
                is_folder=False
            )
        else:
            return FileInfo(
                name=metadata.name,
                path=metadata.path_lower,
                size=0,
                modified="",
                is_folder=True
            )
            
    except Exception as e:
        raise ValueError(f"Failed to get file info for {file_path}: {e}")


@mcp.tool()
def search_file_content(file_paths: List[str], query: str, context_chars: int = 100) -> List[Dict[str, Any]]:
    """
    Search for text within specific files.
    
    Args:
        file_paths: List of file paths to search in
        query: Text to search for
        context_chars: Number of characters of context around matches
    """
    if not dropbox_client:
        initialize_dropbox_client()
    
    results = []
    
    for file_path in file_paths:
        try:
            content = get_file_content(file_path)
            
            # Search for query in content (case-insensitive)
            query_lower = query.lower()
            content_lower = content.lower()
            
            matches = []
            start = 0
            while True:
                pos = content_lower.find(query_lower, start)
                if pos == -1:
                    break
                
                # Extract context around the match
                context_start = max(0, pos - context_chars)
                context_end = min(len(content), pos + len(query) + context_chars)
                context = content[context_start:context_end]
                
                matches.append({
                    "position": pos,
                    "context": context,
                    "line_number": content[:pos].count('\n') + 1
                })
                
                start = pos + 1
            
            if matches:
                results.append({
                    "file_path": file_path,
                    "file_name": file_path.split('/')[-1],
                    "matches": matches,
                    "total_matches": len(matches)
                })
                
        except Exception as e:
            logger.warning(f"Error searching in {file_path}: {e}")
            continue
    
    return results


def main():
    """Main entry point for the HTTP MCP server."""
    print("Dropbox MCP Server starting...")
    
    # Initialize Dropbox client
    try:
        initialize_dropbox_client()
    except Exception as e:
        logger.warning(f"Dropbox client initialization failed: {e}")
        logger.warning("Make sure to set DROPBOX_ACCESS_TOKEN environment variable")
    
    # Setup Starlette app with CORS for cross-origin requests
    app = mcp.streamable_http_app()
    
    # Add CORS middleware for browser-based clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id", "mcp-protocol-version"],
        max_age=86400,
    )
    
    # Get port from environment variable (Smithery sets this to 8081)
    port = int(os.environ.get("PORT", 8080))
    print(f"Listening on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
