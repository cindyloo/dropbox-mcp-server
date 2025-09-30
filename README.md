# Dropbox MCP Server

[![smithery badge](https://smithery.ai/badge/@cindyloo/dropbox-mcp-server)](https://smithery.ai/server/@cindyloo/dropbox-mcp-server)

A Model Context Protocol (MCP) server that provides read access to Dropbox files with advanced search and content extraction capabilities.

## Features

- **File Listing**: Browse files and folders in your Dropbox
- **File Reading**: Read content from various file types (PDF, DOCX, TXT, code files)
- **Search**: Search for files by name across your Dropbox
- **Content Search**: Search for specific text within files
- **File Info**: Get detailed metadata about files
- **Smart Text Extraction**: Automatically extracts text from PDFs and DOCX files

## Supported File Types

- **PDF** - Text extraction with PyPDF2
- **DOCX/DOC** - Document text extraction
- **Text files** - TXT, MD, PY, JS, HTML, CSS, JSON, CSV

## Installation

### Installing via Smithery

To install dropbox-mcp-server automatically via [Smithery](https://smithery.ai/server/@cindyloo/dropbox-mcp-server):

```bash
npx -y @smithery/cli install @cindyloo/dropbox-mcp-server
```

### Prerequisites

- Python 3.10 or higher
- A Dropbox account and access token

### Get a Dropbox Access Token

1. Go to the [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create app"
3. Choose "Scoped access" and "Full Dropbox" access
4. Name your app
5. Go to the "Permissions" tab and enable:
   - `files.metadata.read`
   - `files.content.read`
6. Go to the "Settings" tab and generate an access token

### Install Dependencies

```bash
pip install -e .
```

Or install manually:

```bash
pip install mcp dropbox pydantic PyPDF2 python-docx
```

## Configuration

Set your Dropbox access token as an environment variable:

```bash
export DROPBOX_ACCESS_TOKEN="your_access_token_here"
```

### For Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dropbox": {
      "command": "python",
      "args": ["/path/to/your/dropbox_server.py"],
      "env": {
        "DROPBOX_ACCESS_TOKEN": "your_access_token_here"
      }
    }
  }
}
```

### For Smithery

The server will automatically use the `DROPBOX_ACCESS_TOKEN` environment variable when deployed.

## Available Tools

### `list_files`
List files and folders in a Dropbox directory.

**Parameters:**
- `folder_path` (optional): Path to folder (empty for root)
- `max_files` (optional): Maximum items to return (default: 20)

### `search_files`
Search for files by name.

**Parameters:**
- `query`: Search query
- `file_types` (optional): File types to search ("all", "pdf", "docx", "txt", or comma-separated)
- `max_results` (optional): Maximum results (default: 10)

### `read_file`
Read the full content of a file.

**Parameters:**
- `file_path`: Full path to the file
- `max_length` (optional): Maximum characters to return (default: 5000, 0 for unlimited)

### `get_file_info`
Get detailed metadata about a file.

**Parameters:**
- `file_path`: Full path to the file

### `search_file_content`
Search for text within specific files.

**Parameters:**
- `file_paths`: List of file paths to search
- `query`: Text to search for
- `context_chars` (optional): Characters of context around matches (default: 100)

## Usage Examples

### List files in root directory
```python
list_files()
```

### Search for PDF files
```python
search_files(query="invoice", file_types="pdf", max_results=5)
```

### Read a specific file
```python
read_file(file_path="/documents/report.pdf")
```

### Search within files
```python
search_file_content(
    file_paths=["/documents/file1.txt", "/documents/file2.pdf"],
    query="important keyword"
)
```

## Development

### Running Locally

```bash
python dropbox_server.py
```

### Testing

Make sure your `DROPBOX_ACCESS_TOKEN` is set, then run the server and test with an MCP client.

## Security Notes

- Keep your Dropbox access token secure and never commit it to version control
- Use environment variables or secure secret management
- The server only provides read access to Dropbox files
- Consider using app-scoped tokens with minimal permissions

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
