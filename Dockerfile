# Use an official lightweight Python image
FROM python:3.10-slim

# Set a working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose the port Vercel will route to
EXPOSE 8080

# Run the Flask app with Gunicorn
# queue_app:app → queue_app.py‘s `app = Flask(__name__)`
CMD ["gunicorn", "queue_app:app", "--bind", "0.0.0.0:8080", "--workers", "1"]
