# Use a base Python image
FROM python:3.9-slim

# Copy requirements.txt into the image
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the necessary code files into the image
COPY worker.py /app/worker.py
COPY diagnose_module.py /app/diagnose_module.py
COPY redis_q.py /app/redis_q.py
COPY utils.py /app/utils.py  

# Set the working directory
WORKDIR /app

# Ensure the directory is in the Python path (just in case)
ENV PYTHONPATH /app

# Start the worker
CMD ["python", "worker.py"]
