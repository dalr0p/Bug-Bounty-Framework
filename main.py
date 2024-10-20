import subprocess
import signal
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import os
from urllib.parse import urlparse, parse_qs, urlunparse

# Set up logging to print to console
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Global variable to store running processes
running_processes = []

# Function to handle signal interruptions like CTRL+C
def handle_exit(signum, frame):
    logging.info("Signal received, shutting down all running processes.")
    # Terminate all running subprocesses
    for process in running_processes:
        try:
            logging.info(f"Terminating process {process.pid}")
            process.terminate()
        except Exception as e:
            logging.error(f"Error terminating process: {str(e)}")
    sys.exit(0)

# Register signal handlers for clean exit
signal.signal(signal.SIGINT, handle_exit)  # Handle CTRL+C
signal.signal(signal.SIGTERM, handle_exit)  # Handle kill signal

# Directory to store output files
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ANSI color codes for the logs
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_BLUE = "\033[94m"
COLOR_RESET = "\033[0m"

# ASCII Art for separation
ASCII_ART = """
====================================================
Framework Created by Marcos Ryan Foley Sanchez
====================================================
"""

# Serve the static files from the 'static' directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve HTML frontend to the browser
@app.get("/")
async def get():
    html_content = """
<!DOCTYPE html>
<html>
    <head>
        <title>Bug Bounty Recon</title>
        <link rel="stylesheet" href="/static/styles.css" />
    </head>
    <body>
        <div class="container">
            <h1>Bug Bounty Recon</h1>
            <form id="recon-form">
                <input type="text" id="domain" placeholder="Enter domain" required />
                <button type="submit">Start Recon</button>
            </form>

            <h2 id="logs-title" style="display:none;">Logs</h2>
            <div id="logs" class="logs">
                <!-- Real-time logs will appear here -->
            </div>
            <p class="disclaimer">Note: Only the last 100 log entries are displayed.</p>

            <!-- Hide entire sections initially -->
            <div id="download-subdomains" style="display: none;">
                <h2>Download Subdomains</h2>
                <a id="download-link" href="#" download>Download Subdomains</a>
            </div>

            <div id="download-alive" style="display: none;">
                <h2>Download Alive Subdomains</h2>
                <a id="download-alive-link" href="#" download>Download Alive Subdomains</a>
            </div>

            <div id="download-katana" style="display: none;">
                <h2>Download Katana Output</h2>
                <a id="download-katana-link" href="#" download>Download Katana Output</a>
            </div>

            <div id="download-xss" style="display: none;">
                <h2>Download XSS Results</h2>
                <a id="download-xss-link" href="#" download>Download XSS Results</a>
            </div>

            <script>
                const ws = new WebSocket("ws://" + window.location.host + "/ws");

                ws.onopen = function() {
                    console.log("WebSocket connection established.");
                };

                // Limit log lines to prevent memory overload
                const MAX_LOG_LINES = 100;
                
                // Form submission to start recon
                document.getElementById('recon-form').addEventListener('submit', function(event) {
                    event.preventDefault();
                    const domain = document.getElementById('domain').value;
                    console.log("Starting recon for domain:", domain);
                    ws.send(domain); // Send domain to the WebSocket server
                    document.getElementById('logs-title').style.display = 'block'; // Show the logs title
                });

                // Listen for log messages from the server
                ws.onmessage = function(event) {
                    console.log("Received log:", event.data);

                    const logsDiv = document.getElementById('logs');
                    
                    // Create a new log entry
                    const logEntry = document.createElement('p');
                    
                    // Handle ANSI color codes
                    const message = event.data
                        .replace(/\033\[92m/g, '<span style="color: green;">')  // Green
                        .replace(/\033\[91m/g, '<span style="color: red;">')    // Red
                        .replace(/\033\[94m/g, '<span style="color: blue;">')   // Blue
                        .replace(/\033\[0m/g, '</span>');                       // Reset

                    logEntry.innerHTML = message;

                    // Append new log entry
                    logsDiv.appendChild(logEntry);

                    // Limit log entries to MAX_LOG_LINES
                    const logEntries = logsDiv.getElementsByTagName('p');
                    if (logEntries.length > MAX_LOG_LINES) {
                        logsDiv.removeChild(logEntries[0]);  // Remove the oldest log entry
                    }

                    logsDiv.scrollTop = logsDiv.scrollHeight;  // Auto scroll to the bottom as logs update

                    // Check if the recon is complete and the download link is provided
                    if (event.data.includes("Download link: ")) {
                        const downloadLink = event.data.split("Download link: ")[1];
                        document.getElementById('download-link').href = downloadLink;
                        document.getElementById('download-subdomains').style.display = 'block'; // Show download section
                    }

                    // Check if the alive subdomains download link is provided
                    if (event.data.includes("Download alive link: ")) {
                        const downloadAliveLink = event.data.split("Download alive link: ")[1];
                        document.getElementById('download-alive-link').href = downloadAliveLink;
                        document.getElementById('download-alive').style.display = 'block'; // Show download section
                    }

                    // Check if Katana output is provided
                    if (event.data.includes("Download katana link: ")) {
                        const downloadKatanaLink = event.data.split("Download katana link: ")[1];
                        document.getElementById('download-katana-link').href = downloadKatanaLink;
                        document.getElementById('download-katana').style.display = 'block'; // Show download section
                    }

                    // Check if XSS results download link is provided
                    if (event.data.includes("Download XSS results: ")) {
                        const downloadXSSLink = event.data.split("Download XSS results: ")[1];
                        document.getElementById('download-xss-link').href = downloadXSSLink;
                        document.getElementById('download-xss').style.display = 'block'; // Show download section
                    }
                };

                ws.onerror = function(event) {
                    console.error("WebSocket error observed:", event);
                };

                ws.onclose = function() {
                    console.log("WebSocket connection closed.");
                };
            </script>
        </div>
    </body>
</html>
    """
    return HTMLResponse(content=html_content)

# WebSocket endpoint to stream real-time logs
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connection established.")

    try:
        while True:
            # Receive the domain input from the WebSocket
            domain = await websocket.receive_text()
            logging.info(f"Received domain: {domain}")
            
            # Add ASCII art for separation
            await websocket.send_text(ASCII_ART)

            # Command to run Subfinder
            command = f"subfinder -d {domain}"
            logging.info(f"Running Subfinder command: {command}")

            subdomains = []  # List to store the subdomains

            try:
                # Capture Subfinder output all at once
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    await websocket.send_text(f"Error running Subfinder: {stderr}")
                    logging.error(f"Error running Subfinder: {stderr}")
                    continue

                subdomains = stdout.strip().split("\n")
                logging.info(f"Subfinder found {len(subdomains)} subdomains.")

                # Send subfinder output to the WebSocket
                for subdomain in subdomains:
                    await websocket.send_text(f"Subfinder output: {subdomain}")

                # Save all subdomains to a file
                filename_subdomains = f"{domain}_subdomains.txt"
                filepath_subdomains = os.path.join(OUTPUT_DIR, filename_subdomains)
                with open(filepath_subdomains, 'w') as f:
                    f.write("\n".join(subdomains))

                # Make subdomains file downloadable immediately after Subfinder completes
                await websocket.send_text(f"Download link: /download/{filename_subdomains}")

                # Add separator for `curl` output
                await websocket.send_text(ASCII_ART)

                # Validate subdomains using curl with verbose logging
                alive_subdomains = await validate_subdomains_curl(subdomains, websocket)

                # Save alive subdomains to a file
                filename_alive = f"{domain}_alive_curl.txt"
                filepath_alive = os.path.join(OUTPUT_DIR, filename_alive)
                with open(filepath_alive, 'w') as f:
                    f.write("\n".join(alive_subdomains))

                # Send the download link for alive subdomains
                await websocket.send_text(f"Download alive link: /download/{filename_alive}")

                # Run Katana on the alive subdomains
                katana_output_file = await run_katana_on_alive(alive_subdomains, websocket, domain)

                # Send the download link for Katana output
                await websocket.send_text(f"Download katana link: /download/{katana_output_file}")

                # Notify that Dalfox scan has finished
                await websocket.send_text(f"{COLOR_GREEN}Dalfox XSS scan completed.{COLOR_RESET}")

                # Optionally, provide a download link for Dalfox results (if saved in a file)
                xss_results_file = "dalfox_results.txt"  # Assuming this is where Dalfox results are saved
                await websocket.send_text(f"Download XSS results: /download/{xss_results_file}")

            except Exception as subfinder_error:
                logging.error(f"Error running Subfinder: {str(subfinder_error)}")
                await websocket.send_text(f"Error running Subfinder: {str(subfinder_error)}")

    except WebSocketDisconnect:
        logging.info("Client disconnected. Stopping recon.")
    except Exception as e:
        logging.error(f"Error during WebSocket communication: {str(e)}")

# Validate subdomains using curl with enhanced status code handling and redirect following
async def validate_subdomains_curl(subdomains, websocket):
    alive_subdomains = []
    logging.info("Running curl to validate subdomains...")
    await websocket.send_text(f"{COLOR_GREEN}Running curl to validate subdomains...{COLOR_RESET}")

    try:
        # Prepend both http and https to each subdomain
        urls = [f"http://{sub}" for sub in subdomains] + [f"https://{sub}" for sub in subdomains]

        # Special test for Google to be pinned
        test_url = "http://google.com"
        await websocket.send_text(f"PINNED_TEST: Running curl for test URL: {test_url}")
        logging.info(f"Running curl for test URL: {test_url}")

        # Run curl for Google first to test the status code
        command = f"curl --max-time 10 -L -o /dev/null -s -w '%{{http_code}} %{{url_effective}}' {test_url}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        status_code, final_url = stdout.strip().split(' ', 1)
        if status_code == "200":
            message = f"PINNED_TEST: curl: {final_url} is alive with status {status_code}."
            await websocket.send_text(f"\033[92m{message}\033[0m")
            logging.info(f"curl: {final_url} is alive with status {status_code}.")
        else:
            message = f"PINNED_TEST: curl: {final_url} is not alive or returned status {status_code}."
            await websocket.send_text(f"\033[91m{message}\033[0m")
            logging.info(message)

        if stderr:
            logging.error(f"curl error for {test_url}: {stderr}")
            await websocket.send_text(f"curl error for {test_url}: {stderr}")

        # Now validate the rest of the subdomains
        total_subdomains = len(urls)
        checked_subdomains = 0

        for url in urls:
            checked_subdomains += 1
            progress = f"{COLOR_BLUE}Progress: {checked_subdomains}/{total_subdomains}{COLOR_RESET}"
            await websocket.send_text(progress)  # Send progress update to frontend

            logging.info(f"Running curl for URL: {url}")
            await websocket.send_text(f"Running curl for URL: {url}")

            # Command for curl with a 10-second timeout, following redirects (-L), and capturing the final URL (-w %{url_effective})
            command = ["curl", "--max-time", "10", "-L", "-o", "/dev/null", "-s", "-w", "%{http_code} %{url_effective}", url]

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate()

            if stderr:
                # Log any error output from curl
                message = f"{COLOR_RED}curl error for {url}: {stderr.strip()}{COLOR_RESET}"
                await websocket.send_text(message)
                logging.error(f"curl error for {url}: {stderr.strip()}")
                continue

            # Extract the status code and final URL from the curl output
            output = stdout.strip().split()
            status_code = output[0] if len(output) > 0 else "💀"
            final_url = output[1] if len(output) > 1 else url

            # Check if the final redirected URL is alive (based on 200, 301, 302 status codes)
            if status_code == "200" or status_code in ("301", "302"):
                message = f"{COLOR_GREEN}curl: {final_url} is alive (Status: {status_code}){COLOR_RESET}"
                # Normalize URL to remove path and query params before saving
                normalized_url = normalize_url_no_path(final_url)
                alive_subdomains.append(normalized_url)  # Save the cleaned URL
            elif status_code == "💀":
                message = f"{COLOR_RED}curl: {final_url} is a dead subdomain (Status: {status_code}){COLOR_RESET}"
            else:
                message = f"{COLOR_RED}curl: {final_url} is not alive or returned status {status_code}.{COLOR_RESET}"

            await websocket.send_text(message)
            logging.info(message)

        # Remove duplicates after normalization
        normalized_alive_subdomains = list(set(alive_subdomains))

        return normalized_alive_subdomains

    except Exception as e:
        logging.error(f"Error running curl: {str(e)}")
        await websocket.send_text(f"Error running curl: {str(e)}")

    return alive_subdomains

# Normalize URLs by stripping the path and query parameters
def normalize_url_no_path(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"  # Keep only scheme and domain

# Function to clean Katana output by removing URLs with duplicate parameter names
def clean_katana_output(katana_output_path):
    try:
        # Read the Katana output file
        with open(katana_output_path, 'r') as f:
            katana_urls = f.read().splitlines()

        # Remove duplicates based on parameter names
        cleaned_urls = remove_duplicate_parameter_urls(katana_urls)

        # Overwrite the Katana output file with cleaned URLs
        with open(katana_output_path, 'w') as f:
            f.write("\n".join(cleaned_urls))
        
        logging.info(f"Katana output cleaned and saved to: {katana_output_path}")

    except Exception as e:
        logging.error(f"Error cleaning Katana output: {str(e)}")

# Helper function to remove duplicate URLs based on parameter names
def remove_duplicate_parameter_urls(urls):
    unique_urls = {}
    
    for url in urls:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        # Extract parameter names without their values
        query_params = parse_qs(parsed_url.query)
        param_names = sorted(query_params.keys())  # Sort parameter names for consistency
        
        # Create a key that consists of the base URL and the sorted parameter names
        unique_key = f"{base_url}?{'&'.join(param_names)}" if param_names else base_url
        
        # Store the URL if the parameter set hasn't been encountered yet
        if unique_key not in unique_urls:
            unique_urls[unique_key] = url
    
    return list(unique_urls.values())

# Run Katana on the list of alive subdomains and return the output file path
async def run_katana_on_alive(alive_subdomains, websocket, domain):
    base_output_dir = os.path.abspath("output")
    katana_output_file = f"{domain}_katana.txt"
    katana_output_path = os.path.join(base_output_dir, katana_output_file)  # Full absolute path

    # Ensure the output directory exists
    try:
        if not os.path.exists(base_output_dir):
            os.makedirs(base_output_dir, exist_ok=True)  # Ensure directory exists
            logging.info(f"Created output directory: {base_output_dir}")
        else:
            logging.info(f"Output directory already exists: {base_output_dir}")
    except Exception as e:
        logging.error(f"Error creating output directory: {str(e)}")
        await websocket.send_text(f"{COLOR_RED}Error creating output directory: {str(e)}{COLOR_RESET}")
        return None

    # Ensure the Katana output file exists before running Katana
    try:
        # Create the Katana output file or touch it if it exists
        with open(katana_output_path, 'w') as f:
            pass  # This will create the file if it doesn't exist
        logging.info(f"Katana output file created: {katana_output_path}")
    except Exception as e:
        logging.error(f"Error creating Katana output file: {str(e)}")
        await websocket.send_text(f"{COLOR_RED}Error creating Katana output file: {str(e)}{COLOR_RESET}")
        return None

    logging.info(f"Running Katana on alive subdomains...")

    try:
        alive_subdomains_file = os.path.join(base_output_dir, f"{domain}_alive_curl.txt")
        command = f"katana -list {alive_subdomains_file} -silent"

        # Execute the Katana command and stream the output
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Read Katana output line by line and send it to the WebSocket
        while True:
            line = process.stdout.readline()
            if not line:
                break
            # Send each found URL to the frontend
            await websocket.send_text(f"{COLOR_BLUE}Katana found: {line.strip()}{COLOR_RESET}")

        # Wait for the process to complete
        process.wait()

        if process.returncode != 0:
            stderr = process.stderr.read()
            await websocket.send_text(f"{COLOR_RED}Katana error: {stderr.strip()}{COLOR_RESET}")
            return None

        # Notify that Katana finished and file is being generated
        await websocket.send_text(f"{COLOR_GREEN}Katana has finished discovering URLs. The file is being generated, please stand by...{COLOR_RESET}")

        # Save the full Katana output to a file
        with open(katana_output_path, 'w') as f:
            process = subprocess.Popen(command, shell=True, stdout=f, stderr=subprocess.PIPE, text=True)
            process.communicate()  # Wait until the command finishes

        if os.path.exists(katana_output_path):
            logging.info(f"Katana output saved to: {katana_output_path}")
        else:
            await websocket.send_text(f"{COLOR_RED}Katana output file not found!{COLOR_RESET}")
            return None

        # Notify that cleaning is starting
        await websocket.send_text(f"{COLOR_BLUE}Starting cleanup of Katana output...{COLOR_RESET}")

        # Perform cleanup on the Katana file
        clean_katana_output(katana_output_path)

        # Notify that cleaning is done
        await websocket.send_text(f"{COLOR_GREEN}Katana output cleanup completed.{COLOR_RESET}")

        logging.info(f"Katana scan complete. Output saved to {katana_output_path}.")
        await websocket.send_text(f"Katana scan complete. Output saved to {katana_output_path}.")

    except Exception as e:
        logging.error(f"Error running Katana: {str(e)}")
        await websocket.send_text(f"{COLOR_RED}Error running Katana: {str(e)}{COLOR_RESET}")

    return katana_output_file

# Function to filter URLs with parameters from Katana output
def filter_urls_with_parameters(katana_output_path, domain):
    try:
        # Check if the Katana output file exists
        if not os.path.isfile(katana_output_path):
            logging.error(f"Katana output file does not exist: {katana_output_path}")
            return None

        # Log the file path being processed
        logging.info(f"Processing Katana output file: {katana_output_path}")

        # Read the Katana output file and filter URLs with query parameters
        with open(katana_output_path, 'r') as katana_file:
            katana_urls = katana_file.readlines()

        urls_with_parameters = []
        for url in katana_urls:
            parsed_url = urlparse(url.strip())
            if parsed_url.query:  # Check if URL has query parameters
                urls_with_parameters.append(url.strip())

        # Save the URLs with parameters to a file
        params_file = f"{domain}_parameters.txt"
        params_file_path = os.path.join(OUTPUT_DIR, params_file)
        with open(params_file_path, 'w') as params_output_file:
            params_output_file.write('\n'.join(urls_with_parameters))

        logging.info(f"Filtered URLs with parameters saved to {params_file_path}")
        return params_file_path

    except Exception as e:
        logging.error(f"Error filtering URLs with parameters: {str(e)}")
        return None

# Function to run Dalfox on the filtered URLs and save results
async def run_dalfox_scan(websocket, domain, params_file_path):
    try:
        if not os.path.isfile(params_file_path):
            logging.error(f"Parameters file does not exist: {params_file_path}")
            await websocket.send_text(f"{COLOR_RED}Error: No URLs with parameters found.{COLOR_RESET}")
            return

        # Log that Dalfox scan is starting
        logging.info(f"Running Dalfox scan on {params_file_path}")

        # Output file for Dalfox results
        dalfox_output_file = f"{domain}_dalfox.txt"
        dalfox_output_path = os.path.join(OUTPUT_DIR, dalfox_output_file)

        # Run Dalfox in pipe mode using the filtered URLs
        command = f"cat {params_file_path} | dalfox pipe"
        with open(dalfox_output_path, 'w') as dalfox_output:
            process = subprocess.Popen(command, shell=True, stdout=dalfox_output, stderr=subprocess.PIPE, text=True)

            # Wait for Dalfox process to complete
            process.wait()

        # Check for errors
        if process.returncode == 0:
            logging.info(f"Dalfox scan completed for domain {domain}. Results saved to {dalfox_output_path}")
            await websocket.send_text(f"{COLOR_GREEN}Dalfox scan completed. Results saved to {dalfox_output_file}.{COLOR_RESET}")
        else:
            stderr = process.stderr.read()
            logging.error(f"Dalfox encountered an error: {stderr}")
            await websocket.send_text(f"{COLOR_RED}Error during Dalfox scan: {stderr}{COLOR_RESET}")

        # Provide download link for Dalfox results
        await websocket.send_text(f"Download Dalfox results: /download/{dalfox_output_file}")

    except Exception as e:
        logging.error(f"Error running Dalfox: {str(e)}")
        await websocket.send_text(f"{COLOR_RED}Error running Dalfox: {str(e)}{COLOR_RESET}")

# Endpoint to download the subdomains file
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename)
    return {"error": "File not found"}
