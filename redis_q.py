import uuid
import json  # Added import for JSON operations
import redis
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from utils import save_diagnosis_result


# Connect to the Redis server
try:
    redis_queue = redis.StrictRedis(host='9.59.199.189', port=6379, decode_responses=True)
    redis_queue.ping()  # Check if the connection is successful
    print("Connected to Redis")
except redis.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")

# Function to add URLs to the Redis queue
def add_urls_to_redis(urls):
    job_id = str(uuid.uuid4())  # Generate a unique job ID
    url_list = [url.strip() for url in urls.split('\n') if url.strip()]  # Clean and split the input string into a list of URLs

    if url_list:  # Ensure there are URLs to push
        redis_queue.lpush(f'url_queue:{job_id}', *url_list)  # Push the list of URLs as a batch into the Redis list
        total_urls = len(url_list)
        print(f"URLs pushed to Redis queue: {url_list}")  # Log the list of URLs that were pushed

        # Store the total number of URLs in Redis
        redis_queue.set(f'total_urls:{job_id}', total_urls)
        redis_queue.set(f'diagnosed_urls:{job_id}', 0)  # Initialize the diagnosed URLs count to 0

        return job_id  # Return the generated job ID
    else:
        print("No valid URLs provided.")
        return None


# Function to retrieve diagnosis results for a job from Redis
def get_diagnosis_results(job_id):
    results = redis_queue.hgetall(f'diagnosis:{job_id}')  # Retrieve all results for the job ID from Redis
    structured_results = []

    for url, result_str in results.items():
        result = json.loads(result_str)  # Convert the JSON string back to a dictionary
        structured_results.append(result)

    return structured_results  # Return the list of structured results

# Function to check the status of a job
def get_job_status(job_id):
    # Wait until the total_urls key is set in Redis
    total_urls_str = None
    attempts = 0
    while total_urls_str is None and attempts < 5:  # Maximum of 5 attempts
        total_urls_str = redis_queue.get(f'total_urls:{job_id}')
        if total_urls_str is None:
            print(f"Waiting for total_urls to be set for job_id {job_id}. Attempt {attempts + 1}/5")
            time.sleep(1)  # Wait 1 second before trying again
            attempts += 1

    if total_urls_str is None:
        print(f"Error: total_urls for job_id {job_id} not found in Redis.")
        return False

    diagnosed_urls_str = redis_queue.get(f'diagnosed_urls:{job_id}')

    if diagnosed_urls_str is None:
        print(f"Error: diagnosed_urls for job_id {job_id} not found in Redis.")
        return False

    total_urls = int(total_urls_str)
    diagnosed_urls = int(diagnosed_urls_str)
    print(f"Checking job status: Diagnosed URLs: {diagnosed_urls}/{total_urls}")  # Debugging output
    return diagnosed_urls >= total_urls  # Return True if all URLs have been diagnosed
