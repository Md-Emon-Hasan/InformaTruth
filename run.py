import subprocess
import sys
import os
import signal
import time
import threading

# Global flag for shutdown
shutdown_flag = False

def stream_output(process, prefix):
    """Reads output from a subprocess and prints it with a prefix."""
    try:
        for line in iter(process.stdout.readline, ''):
            if shutdown_flag:
                break
            if line:
                print(f"[{prefix}] {line.strip()}")
    except Exception:
        pass

def main():
    global shutdown_flag
    print("Welcome to InformaTruth Runner (Local Mode)")
    print("Starting services from local files...")

    # Define paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    # Start Backend
    print("\n[Launcher] Starting Backend (FastAPI)...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=backend_dir,
        shell=False, # Use shell=False for direct execution
    )

    # Start Frontend
    print("[Launcher] Starting Frontend (Vite)...")
    # Use 'npm.cmd' on Windows, 'npm' on others
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]
    frontend_process = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_dir,
        shell=False
    )

    print("\n[Launcher] Both services started.")
    print("[Launcher] Backend: http://127.0.0.1:8000")
    print("[Launcher] Frontend: http://localhost:5173 (usually)")
    print("[Launcher] Press Ctrl+C to stop both services.\n")

    try:
        while True:
            time.sleep(1)
            # Check if any process has exited unexpectedly
            if backend_process.poll() is not None:
                print("[Launcher] Backend stopped unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("[Launcher] Frontend stopped unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n[Launcher] Stopping services...")
        shutdown_flag = True
    finally:
        # Terminate processes
        if backend_process.poll() is None:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        if frontend_process.poll() is None:
            # On Windows, npm might spawn child processes that don't die with terminate
            # But simple terminate works for dev scenarios usually.
            # Using taskkill for robust cleanup on Windows if needed, but start with terminate.
            frontend_process.terminate()
             # If using shell=True, we might need to kill process group. 
             # With shell=False and npm.cmd, terminate might leave node running.
             # Improvement:
            if sys.platform == 'win32':
                 subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                frontend_process.terminate()
        
        print("[Launcher] Services stopped.")

if __name__ == "__main__":
    main()
