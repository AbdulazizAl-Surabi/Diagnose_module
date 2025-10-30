from flask import Flask, request, render_template, jsonify
from redis_q import add_urls_to_redis, get_diagnosis_results, get_job_status
import subprocess
import uuid
import redis

app = Flask(__name__)

# Try to connect to the Redis server
try:
    redis_queue = redis.StrictRedis(host='9.59.199.189', port=6379, decode_responses=True)
    redis_queue.ping()  # Ping Redis to ensure the connection is successful
    print("Connected to Redis")
except redis.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")

# Function to build the Docker image for the worker containers
def build_docker_image():
    try:
        subprocess.run(["docker", "build", "-t", "url-worker", "."], check=True)
        print("Docker image 'url-worker' was successfully built")
    except subprocess.CalledProcessError as e:
        print(f"Error building Docker image: {e}")

# Function to start the worker containers
def start_worker_containers(num_workers=2):
    for i in range(num_workers):
        worker_id = f"url-worker-{uuid.uuid4().hex[:8]}"  # Generate a unique worker ID
        try:
            subprocess.run(["docker", "run", "-d", "--name", worker_id, "url-worker"], check=True)
            print(f"Worker container {worker_id} started")
        except subprocess.CalledProcessError as e:
            print(f"Error starting worker container {worker_id}: {e}")

# Define the route for the main page
@app.route('/')
def index():
    return render_template('index.html')  # Render the index page

# Define the route for starting the diagnosis and redirecting to the waiting page
@app.route('/start_diagnosis', methods=['POST'])
def start_diagnosis():
    urls = request.form.get('urls')  # Get the URLs submitted by the user
    job_id = add_urls_to_redis(urls)  # Add the URLs to Redis and get a job ID
    return jsonify({"job_id": job_id})  # Return the job ID as JSON

# Define the route for the waiting page
@app.route('/waiting/<job_id>')
def waiting(job_id):
    return render_template('waiting.html', job_id=job_id)  # Render the waiting page with job_id

# Define the route to check the total number of URLs for a job
@app.route('/check_total_urls/<job_id>')
def check_total_urls(job_id):
    total_urls = redis_queue.get(f'total_urls:{job_id}')  # Get the total URLs for the job from Redis
    if total_urls:
        return jsonify({"success": True, "total_urls": total_urls})
    else:
        return jsonify({"success": False, "message": f"total_urls for job_id {job_id} not set"})

# Define the route to check the status of a job (whether it's completed)
@app.route('/check_status/<job_id>')
def check_status(job_id):
    diagnosed_urls_str = redis_queue.get(f'diagnosed_urls:{job_id}')
    diagnosed_urls = int(diagnosed_urls_str) if diagnosed_urls_str else 0
    total_urls_str = redis_queue.get(f'total_urls:{job_id}')
    total_urls = int(total_urls_str) if total_urls_str else 0

    return jsonify({
        "done": diagnosed_urls >= total_urls,
        "diagnosed_urls": diagnosed_urls
    })

# Define the route to check if a job is fully completed
@app.route('/check_job_completion/<job_id>')
def check_job_completion(job_id):
    completed = redis_queue.get(f'job_completed:{job_id}') == 'true'
    return jsonify({"completed": completed})

# Define the route to show the diagnosis results
@app.route('/diagnose_urls/<job_id>')
def diagnose_urls(job_id):
    results = get_diagnosis_results(job_id)  # Get the diagnosis results from Redis
    return render_template('results.html', results=results, job_id=job_id)  # Render the results page

if __name__ == '__main__':
    build_docker_image()  # Build the Docker image when the app starts
    start_worker_containers(num_workers=1)  # Start one worker container
    app.run(debug=True, port=5001)
