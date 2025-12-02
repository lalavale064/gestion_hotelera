FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web/ ./web/
COPY db_init/ ./db_init/
COPY hotel_data_inserts.sql .
COPY fix_encoding.sql .

# Set working directory to web
WORKDIR /app/web

# Expose port
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
