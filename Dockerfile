# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variable for PYTHONPATH
ENV PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask runs on
EXPOSE 5000

# Default command to run the Flask app
CMD ["python", "app.py"]