import os
import signal
import subprocess
import time
import uvicorn

MAX_ATTEMPTS = 3  # Number of retry attempts to kill the process

# Function to kill process using a specific port
def kill_process_on_port(port, max_attempts):
    for attempt in range(1, max_attempts + 1):
        try:
            # Get the PID of the process using the port
            result = subprocess.run(
                ["lsof", "-t", f"-i:{port}"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            pid = result.stdout.strip()

            if pid:
                print(f"Attempt {attempt}: Port {port} is in use by process {pid}. Killing the process.")
                os.kill(int(pid), signal.SIGTERM)
                time.sleep(2)

                # Check if the port is free now
                result = subprocess.run(
                    ["lsof", "-t", f"-i:{port}"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                if not result.stdout.strip():
                    print(f"Process {pid} killed. Port {port} is now free.")
                    return True
            else:
                print(f"Port {port} is free.")
                return True

        except Exception as e:
            print(f"Error while trying to free port {port}: {e}")

    print(f"Failed to free port {port} after {max_attempts} attempts.")
    return False

# Function to find the next available port starting from a given port
def find_next_available_port(start_port=8000):
    port = start_port
    while True:
        result = subprocess.run(
            ["lsof", "-t", f"-i:{port}"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        if not result.stdout.strip():
            return port
        port += 1

# Try to free port 8000, and if it fails, find the next available port
if not kill_process_on_port(8000, MAX_ATTEMPTS):
    port = find_next_available_port(8001)
    print(f"Running FastAPI app on the next available port: {port}")
else:
    port = 8000

# Run the FastAPI app with Uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
