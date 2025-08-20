FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libgbm1 \
    libgtk-3-0 \
    jq \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Add Google's official GPG key and repository
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install the latest stable version of Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable

# Install ChromeDriver using the new Chrome for Testing API
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    echo "Chrome version: $CHROME_VERSION" && \
    CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
    jq -r ".versions[] | select(.version==\"$CHROME_VERSION\") | .downloads.chromedriver[] | select(.platform==\"linux64\") | .url" | head -1) && \
    if [ -z "$CHROMEDRIVER_URL" ]; then \
        echo "Exact version not found, getting latest stable ChromeDriver..." && \
        CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json" | \
        jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url'); \
    fi && \
    echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL" && \
    wget -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    find /tmp -name "chromedriver" -type f -exec mv {} /usr/local/bin/ \; && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver* && \
    chromedriver --version

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LANG C.UTF-8

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run both UI and scraping script
CMD ["sh", "-c", "uvicorn ui_server:app --host 0.0.0.0 --port 8000 & python main.py"]