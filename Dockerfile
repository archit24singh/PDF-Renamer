# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that your app will run on (Fly.io expects 8080 by default)
EXPOSE 8080

# Use gunicorn to serve the app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
