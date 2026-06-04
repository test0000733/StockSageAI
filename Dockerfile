FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY StockSageAI/ /app/StockSageAI/

# Create .streamlit directory and copy config
RUN mkdir -p /app/.streamlit
COPY StockSageAI/.streamlit/config.toml /app/.streamlit/

# Copy any data files (explicit list avoids shell fallback which is invalid in Dockerfile)
# If you add more CSVs, include them here or copy the folder instead.
COPY ["EQUITY_L.csv", "EQUITY_L(in).csv", "/app/"]

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Expose port
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run Streamlit app. Render or CI can override start command.
CMD ["streamlit", "run", "StockSageAI/app.py"]
