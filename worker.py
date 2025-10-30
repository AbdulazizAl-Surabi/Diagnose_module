import redis
import webbrowser
from diagnose_module import check_url, check_robots_txt, check_sitemap
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from utils import save_diagnosis_result

redis_queue = redis.StrictRedis(host='9.59.199.189', port=6379, decode_responses=True)

def worker_process():
    print("Connected to Redis")
    print("Worker process started...")
    
    while True:
        job_keys = redis_queue.keys('url_queue:*')
        print(f"Found job keys: {job_keys}")
        
        for job_key in job_keys:
            url = redis_queue.rpop(job_key)
            if url:
                print(f"Processing URL: {url}")
                
                # Check if the URL has already been diagnosed (redundancy check)
                if redis_queue.hexists(f'diagnosis:{job_key.split(":")[-1]}', url):
                    print(f"URL {url} already diagnosed, skipping...")
                    continue
                
                # Initialize result dictionary
                result = {"url": url, "connection": "", "robots_txt": "", "sitemap": ""}
                
                # Check connection
                print("[DEBUG] Checking connection...")
                connection_result, headers = check_url(url)
                result["connection"] = connection_result
                print(f"[DEBUG] Connection result: {result['connection']}")

                if headers:
                    # Check robots.txt
                    print("[DEBUG] Checking robots.txt...")
                    robots_txt_result = check_robots_txt(url, headers)
                    result["robots_txt"] = robots_txt_result
                    print(f"[DEBUG] robots.txt result: {result['robots_txt']}")
                
                    # Check sitemap and also return found sitemaps from robots.txt
                    print("[DEBUG] Checking sitemap...")
                    sitemap_result, found_sitemaps = check_sitemap(url, headers)
                    result["sitemap"] = sitemap_result
                    if found_sitemaps:
                        result["robots_txt"] += f" | Sitemaps found: {', '.join(found_sitemaps)}"
                    print(f"[DEBUG] Sitemap result: {result['sitemap']}")
                else:
                    result["robots_txt"] = "Failed to connect"
                    result["sitemap"] = "Failed to connect"
                    print("[DEBUG] Failed to connect, skipping robots.txt and sitemap checks.")
                
                # Save the result in Redis (this should only happen once per URL)
                save_diagnosis_result(job_key.split(":")[-1], url, result)
                
                # Debugging output: Print the saved result
                print(f"Saved diagnosis result for {url}: {result}")
                
                total_urls_str = redis_queue.get(f"total_urls:{job_key.split(':')[-1]}")
                total_urls = int(total_urls_str) if total_urls_str is not None else 0
                diagnosed_urls_str = redis_queue.get(f"diagnosed_urls:{job_key.split(':')[-1]}")
                diagnosed_urls = int(diagnosed_urls_str) if diagnosed_urls_str is not None else 0
                print(f"Diagnosed URLs: {diagnosed_urls}/{total_urls}")
                
                # Mark job as completed if all URLs are diagnosed
                if diagnosed_urls >= total_urls:
                    redis_queue.set(f"job_completed:{job_key.split(':')[-1]}", "true")
                    print(f"All URLs diagnosed for job {job_key.split(':')[-1]}.")
                    
                    # Open the results page in the browser
                    results_url = f"http://127.0.0.1:5001/diagnose_urls/{job_key.split(':')[-1]}"
                    webbrowser.open(results_url)

if __name__ == "__main__":
    worker_process()

