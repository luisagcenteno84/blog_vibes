# Use the official Python image as a base image
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Set the FLASK_APP environment variable
ENV FLASK_APP=run.py

# Expose the port that Flask will run on
EXPOSE 8080

# Command to run the application
# Gunicorn is a production-ready WSGI server, recommended for Flask deployments
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "run:app"]
