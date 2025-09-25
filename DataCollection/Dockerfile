FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && chmod +x chromedriver \
    && mv chromedriver /usr/local/bin/ \
    && rm chromedriver_linux64.zip

# Set working directory
WORKDIR /app

# Copy requirements files
COPY DynamoToOpensearch/requirements.txt /app/requirements_dynamo.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_dynamo.txt \
    && pip install --no-cache-dir \
        selenium \
        beautifulsoup4 \
        requests \
        boto3 \
        apache-airflow==2.7.3

# Copy the DataCollection directory
COPY . /app/DataCollection/

# Set PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create airflow directories
RUN mkdir -p /app/logs /app/dags /app/plugins

# Set airflow home
ENV AIRFLOW_HOME=/app

# Initialize airflow database (for standalone mode)
RUN airflow db init

# Create airflow user
RUN airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

# Expose airflow webserver port
EXPOSE 8080

# Default command to run airflow webserver and scheduler
CMD ["bash", "-c", "airflow webserver --port 8080 & airflow scheduler"]