# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 and build tools
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole repo
COPY . .

EXPOSE 8501

# Default command (can be overridden)
CMD ["python", "-m", "pulse", "run", "--pipeline", "all"]
