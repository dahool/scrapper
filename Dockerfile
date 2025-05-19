# Use an official Python runtime as a parent image (choose a specific version)
FROM python:3.9-slim

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive \
    # Set path for python output to appear immediately
    PYTHONUNBUFFERED=1
ENV LANG=en_US.UTF-8

# Install system dependencies required for Chrome and ChromeDriver
# Using Debian/Ubuntu package manager (apt-get)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Utilities
    wget \
    unzip \
    ca-certificates \
    # Chrome dependencies
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    # Install Google Chrome Stable
    && echo "Downloading Google Chrome..." \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && echo "Installing Google Chrome..." \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    # --- ChromeDriver Installation ---
    # Get the installed Chrome version
    && CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E 's/.* ([0-9]+)\..*/\1/') \
    && echo "Detected Chrome major version: $CHROME_MAJOR_VERSION" \
    # Get the latest ChromeDriver version for the installed Chrome major version
    # Note: This URL might change. Check https://googlechromelabs.github.io/chrome-for-testing/
    && CHROMEDRIVER_VERSION=$(wget -qO- "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR_VERSION}") \
    && echo "Using ChromeDriver version: $CHROMEDRIVER_VERSION" \
    # Download and install ChromeDriver
    && echo "Downloading ChromeDriver..." \
    && wget -q https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip \
    && echo "Installing ChromeDriver..." \
    && unzip chromedriver-linux64.zip -d /usr/local/bin/ \
    # The zip might contain a directory, so move the executable if needed
    && mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm chromedriver-linux64.zip \
    && rm -rf /usr/local/bin/chromedriver-linux64 \
    && chmod +x /usr/local/bin/chromedriver \
    # --- Cleanup ---
    && echo "Cleaning up apt cache..." \
    #&& apt-get purge -y --auto-remove wget unzip \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install Python dependencies
# Using pip without cache to keep the image smaller
RUN pip install --no-cache-dir selenium beautifulsoup4

# Copy the Python script into the container's working directory
COPY scrap.py .

# Define the command to run the Python script when the container starts
# This executes: python scraper.py
CMD ["python", "scrap.py"]

