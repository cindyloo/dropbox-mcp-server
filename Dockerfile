# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY dropbox_server.py ./

# Create non-root user for security
RUN useradd -m -u 1000 mcpuser && \
    chown -R mcpuser:mcpuser /app

USER mcpuser

# Expose port (Smithery uses PORT env var, defaults to 8081)
EXPOSE 8081

# Run the server
CMD ["python", "dropbox_server.py"]