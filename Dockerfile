# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts are executable
RUN chmod +x /app/*.py || true

# Update PATH to include user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Expose port (Cloud Run uses PORT environment variable)
EXPOSE 8080

# Set default PORT for Cloud Run
ENV PORT=8080

# Run the application using PORT environment variable
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
