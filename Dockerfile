# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy application code first
COPY dropbox_server.py ./
COPY pyproject.toml ./

# Install dependencies directly from pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    "mcp>=0.1.0" \
    "dropbox>=12.0.0" \
    "pydantic>=2.0.0" \
    "PyPDF2>=3.0.0" \
    "python-docx>=1.0.0" \
    "uvicorn>=0.27.0" \
    "starlette>=0.35.0"

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# Expose port (Smithery uses PORT env var, defaults to 8081)
EXPOSE 8081

# Run the server
CMD ["python", "dropbox_server.py"]