# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    adb \
    openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Maestro (optional, since our runner uses adb mostly, but good to have)
RUN curl -Ls "https://get.maestro.mobile.dev" | bash
ENV PATH="/root/.maestro/bin:$PATH"

# Set the working directory
WORKDIR /app
RUN mkdir -p /test-flows

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
