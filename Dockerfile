FROM python:3.11-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Manim
RUN apt-get update && apt-get install -y \
    ffmpeg \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    libcairo2-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    pkg-config \
    python3-dev \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create renders directory
RUN mkdir -p renders

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status')" || exit 1

# Run the application
CMD ["python", "app.py"]
