FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml run_web.sh ./
COPY jarbas/ ./jarbas/
COPY config.yaml ./

# Make run_web.sh executable
RUN chmod +x run_web.sh

# Install dependencies using pip with explicit flags
RUN pip install --no-cache-dir setuptools wheel
RUN pip install --no-cache-dir -e .
RUN pip list

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Port for Streamlit
EXPOSE 8501

# Run the web interface by default
CMD ["streamlit", "run", "jarbas/main_web.py"] 