# Use Python as base image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy only the files from the specific GitHub folder
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command
#CMD ["python", "main.py",""]