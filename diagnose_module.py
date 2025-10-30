import requests
import xmltodict
import urllib.robotparser
import json
from urllib.parse import urlparse, urlunparse
import time

# List of Linux, Windows, and Mac User Agents
USER_AGENTS = [
    # Linux User Agents
    "Mozilla/5.0 (X11; Linux i686; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    
    # Windows User Agents
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",

    # Mac User Agents
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Gecko/20100101 Firefox/125.0"
]

def check_url(url):
    last_exception = None
    cloudflare_detected = False  # Flag to detect Cloudflare
    GREEN = '<span class="text-green">'
    RED = '<span class="text-red">'
    ENDC = '</span>'

    for user_agent in USER_AGENTS:
        headers = {"User-Agent": user_agent}  # Update headers for each user agent
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            if 'Server' in response.headers and 'cloudflare' in response.headers['Server'].lower() and response.status_code == 403:
                cloudflare_detected = True
                return f"{RED}Connection blocked by Cloudflare:{ENDC} {response.status_code} {response.reason} for url: {url} with User-Agent: {user_agent}", headers

            return f"{GREEN}Connection successful:{ENDC} {url} with User-Agent: {user_agent}", headers

        except requests.exceptions.HTTPError as http_err:
            last_exception = http_err
            
            if 'Server' in response.headers and 'cloudflare' in response.headers['Server'].lower() and response.status_code == 403:
                cloudflare_detected = True
                return f"{RED}Connection blocked by Cloudflare:{ENDC} {http_err}", headers

        except requests.exceptions.SSLError as ssl_err:
            last_exception = ssl_err
            return f"{RED}Failed to connect due to SSL error:{ENDC} {ssl_err} after trying all user agents.", None

        except requests.exceptions.RequestException as req_err:
            last_exception = req_err

    if cloudflare_detected:
        return f"{RED}Failed to connect due to Cloudflare block after trying all user agents.{ENDC} Exception: {last_exception}", None
    elif isinstance(last_exception, requests.exceptions.SSLError):
        return f"{RED}Failed to connect due to SSL error:{ENDC} {last_exception} after trying all user agents.", None
    else:
        return f"{RED}Failed to connect with all user agents.{ENDC} Exception: {last_exception}", None


# Function to sanitize URL by stripping the path, keeping only the base domain
def sanitize_url(url):
    parsed_url = urlparse(url)
    sanitized_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
    return sanitized_url

def check_robots_txt(url, headers):
    sanitized_url = sanitize_url(url)
    robots_url = f"{sanitized_url}/robots.txt"
    GREEN = '<span class="text-green">'
    RED = '<span class="text-red">'
    ENDC = '</span>'
    try:
        response = requests.get(robots_url, headers=headers, timeout=10)
        response.raise_for_status()
        return f"{GREEN}robots.txt successfully retrieved{ENDC}"
    except Exception as e:
        return f"{RED}Error retrieving robots.txt:{ENDC} {e}"

# Function to retrieve and parse a sitemap XML file
def get_site_xml(sitemap, headers):
    try:
        response = requests.get(sitemap, headers=headers, timeout=10)
        response.raise_for_status()
        _json = xmltodict.parse(response.content)
        return _json, response.status_code
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP Error when accessing sitemap: {http_err}")
        return None, response.status_code
    
    except requests.exceptions.RequestException as req_err:
        print(f"Request Exception when accessing sitemap: {req_err}")
        return None, None
    except Exception as e:
        print(f"Error retrieving or parsing sitemap: {e}")
        return None, None
    
def check_sitemap(url, headers):
    sanitized_url = sanitize_url(url)
    robots_url = f"{sanitized_url}/robots.txt"
    sitemap_source = ""
    found_sitemaps = []
    sitemap_variations = [
        "sitemap.xml",
        "sitemap_index.xml",
        "sitemapindex.xml",
        "sitemap",
        "sitemap-index.xml",
        "sitemap/index.xml",
        "sitemap/sitemap.xml",
        "sitemap1.xml",
    ]
    parsing_errors = []
    sitemap_results = []
    timeout_occurred = False
    start_time = time.time()

    def process_sitemap_recursive(sitemap_url, is_robot_sitemap=False):
        nonlocal parsing_errors, sitemap_results, timeout_occurred
        print(f"[DEBUG] Processing sitemap: {sitemap_url}")
        
        elapsed_time = time.time() - start_time
        if elapsed_time > 180:
            timeout_occurred = True
            timeout_message = "Timeout after 3min threshold"
            print(f"[DEBUG] Sitemap URL: {sitemap_url} - {timeout_message}")
            if not sitemap_results or sitemap_results[-1] != f"<a href='{sitemap_url}'>{sitemap_url}</a> - {timeout_message}":
                sitemap_results.append(f"<a href='{sitemap_url}'>{sitemap_url}</a> - {timeout_message}")
            return False
        
        try:
            _json, status_code = get_site_xml(sitemap_url, headers)
            if not _json:
                if status_code == 404 and is_robot_sitemap:
                    error_message = "404 Not Found"
                    print(f"[DEBUG] Sitemap URL: {sitemap_url} - {error_message}")
                    parsing_errors.append(error_message)
                    sitemap_results.append(f"<a href='{sitemap_url}'>{sitemap_url}</a> - {error_message}")
                elif status_code:
                    error_message = f"Failed with status code: {status_code}"
                    print(f"[DEBUG] Sitemap URL: {sitemap_url} - {error_message}")
                    parsing_errors.append(error_message)
                    sitemap_results.append(f"<a href='{sitemap_url}'>{sitemap_url}</a> - {error_message}")
                else:
                    error_message = "Error retrieving or parsing sitemap: XML or text declaration not at start of entity"
                    print(f"[DEBUG] Sitemap URL: {sitemap_url} - {error_message}")
                    parsing_errors.append(error_message)
                    sitemap_results.append(f"<a href='{sitemap_url}'>{sitemap_url}</a> - {error_message}")
                return False
            else:
                success_message = "Successfully parsed"
                print(f"[DEBUG] Sitemap URL: {sitemap_url} - {success_message}")
                sitemap_results.append(f"<a href='{sitemap_url}'>{sitemap_url}</a> - {success_message}")

                if 'sitemapindex' in _json and not timeout_occurred:
                    print(f"[DEBUG] Found nested sitemapindex in {sitemap_url}")
                    sitemaps = _json['sitemapindex'].get('sitemap', [])
                    if isinstance(sitemaps, dict):
                        sitemaps = [sitemaps]
                    for sitemap_entry in sitemaps:
                        nested_sitemap_url = sitemap_entry['loc']
                        if timeout_occurred:
                            break
                        process_sitemap_recursive(nested_sitemap_url)
                return True
        except Exception as e:
            error_message = f"Error retrieving or parsing sitemap: {str(e)}"
            print(f"[DEBUG] Sitemap URL: {sitemap_url} - {error_message}")
            parsing_errors.append(error_message)
            sitemap_results.append(f"<a href='{sitemap_url}'>{sitemap_url}</a> - {error_message}")
            return False

    try:
        print(f"[DEBUG] Checking robots.txt at {robots_url}")
        response = requests.get(robots_url, headers=headers, timeout=10)
        response.raise_for_status()
        robotparser = urllib.robotparser.RobotFileParser()
        robotparser.parse(response.text.splitlines())
        sitemaps = robotparser.site_maps()

        if sitemaps:
            sitemap_source = "from robots.txt"
            print(f"[DEBUG] Sitemaps found in robots.txt: {sitemaps}")
            found_sitemaps.extend(sitemaps)
            for sitemap in sitemaps:
                if timeout_occurred:
                    break
                if sitemap.startswith('/'):
                    sitemap = f"{sanitized_url}{sitemap}"
                print(f"[DEBUG] Found sitemap: {sitemap} ({sitemap_source})")
                process_sitemap_recursive(sitemap, is_robot_sitemap=True)
        else:
            print("[DEBUG] No sitemaps found in robots.txt. Checking common variations...")
            found_any_variation = False
            for variation in sitemap_variations:
                if timeout_occurred:
                    break
                sitemap_url = f"{sanitized_url}/{variation}"
                print(f"[DEBUG] Trying sitemap: {sitemap_url} ({sitemap_source})")
                if process_sitemap_recursive(sitemap_url):
                    found_any_variation = True

            if not found_any_variation:
                print("[DEBUG] No sitemaps found with common variations")
                sitemap_results.append("No sitemaps found with common variations")

        if parsing_errors:
            error_messages = " | ".join(parsing_errors)
            print(f"[DEBUG] Parsing errors encountered in sitemaps {sitemap_source}: {error_messages}")
        return "<br>".join(sitemap_results), found_sitemaps
    except Exception as e:
        error_message = f"Error checking sitemap {sitemap_source}: {str(e)}"
        print(f"[DEBUG] {error_message}")
        return error_message, found_sitemaps


# Function to parse URLs from a sitemap XML
def parse_sitemap_urls(_json):
    def alt_href(elt):
        alt = []
        if 'xhtml:link' in elt:
            if isinstance(elt['xhtml:link'], list):
                for x in elt['xhtml:link']:
                    if '@href' in x:
                        alt.append(x['@href'])
            else:
                x = elt['xhtml:link']
                if '@href' in x:
                    alt = [x['@href']]
        return alt
    
    if 'urlset' in _json and 'url' in _json['urlset']:
        if isinstance(_json['urlset']['url'], list):
            loc = []
            alt = []
            for elt in _json['urlset']['url']:
                loc.append(elt['loc'])
                alt.extend(alt_href(elt))
            return loc, alt
        else:
            elt = _json['urlset']['url']
            return [elt['loc']], alt_href(elt)
    return None, None
