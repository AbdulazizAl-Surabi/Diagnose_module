import json
import redis
from redlock import Redlock

# Connect to the Redis server
try:
    redis_queue = redis.StrictRedis(host='9.59.199.189', port=6379, decode_responses=True)
    redis_queue.ping()  # Check if the connection is successful
    print("Connected to Redis")
except redis.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")

# Initialize Redlock for distributed locking
dlm = Redlock([{"host": "9.59.199.189", "port": 6379, "db": 0}])

# Function to save diagnosis results for a URL and update the diagnosed URLs count
def save_diagnosis_result(job_id, url, result):
    result_str = json.dumps(result)
    redis_queue.hset(f'diagnosis:{job_id}', url, result_str)
    
    # Use Redlock to ensure atomic increment of the diagnosed URLs count
    lock = dlm.lock(f"lock:{job_id}", 1000)
    if lock:
        try:
            total_urls_str = redis_queue.get(f'total_urls:{job_id}')
            if total_urls_str is None:
                print(f"Error: total_urls for job_id {job_id} not found in Redis.")
                return
            
            diagnosed_urls = redis_queue.incr(f'diagnosed_urls:{job_id}')  # Increment the diagnosed URL count
            total_urls = int(total_urls_str)

            print(f"Diagnosis result saved for {url}: {result_str}")  # Debugging output
            print(f"Diagnosed URLs: {diagnosed_urls}/{total_urls}")  # Debugging output

            if diagnosed_urls > total_urls:
                print(f"Warning: Diagnosed URLs ({diagnosed_urls}) exceeded Total URLs ({total_urls}) for job {job_id}")
                # Add additional handling or checks here if needed
        finally:
            dlm.unlock(lock)
