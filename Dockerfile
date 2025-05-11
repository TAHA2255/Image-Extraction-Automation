# Use Python base image
FROM python:3.10-slim

# Install tesseract and required tools
RUN apt-get update && \
    apt-get install -y tesseract-ocr libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /main

# Copy all project files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose the port your app runs on
EXPOSE 5000

# Run the app (adjust this if using something else like uvicorn for FastAPI)
CMD ["python", "main.py"]
