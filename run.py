import os
import sys
import time
import subprocess
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
VENV_DIR = BASE_DIR / "venv"

# Use venv python
if os.name == "nt":
    PYTHON = VENV_DIR / "Scripts" / "python.exe"
else:
    PYTHON = VENV_DIR / "bin" / "python"

def bootstrap():
    """Setup venv and install dependencies."""
    print(">> Initializing environment...")

    # 1. Ensure venv exists
    if not VENV_DIR.exists():
        print(">> Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

    # 2. Install backend deps
    reqs = BACKEND_DIR / "requirements.txt"
    if reqs.exists():
        print(">> Syncing backend dependencies...")
        subprocess.run([str(PYTHON), "-m", "pip", "install", "-q", "-r", str(reqs)])

    # 3. Install frontend deps
    if not (FRONTEND_DIR / "node_modules").exists():
        print(">> node_modules missing. Running npm install...")
        npm = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.run([npm, "install"], cwd=FRONTEND_DIR, shell=(os.name == "nt"), check=True)

    # 4. Model pointer check
    model = BACKEND_DIR / "fine_tuned_liar_detector" / "adapter_model.safetensors"
    if model.exists() and model.stat().st_size < 1024 * 1024:
        print("\n[!] WARNING: adapter_model.safetensors is a Git LFS pointer.")
        print("[!] Please download the actual 4.7MB file manually.\n")

def run():
    bootstrap()
    
    print("\n>> Booting services...")
    
    # Start Backend
    be_proc = subprocess.Popen(
        [str(PYTHON), "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"],
        cwd=BACKEND_DIR
    )

    # Start Frontend
    npm = "npm.cmd" if os.name == "nt" else "npm"
    fe_proc = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=FRONTEND_DIR,
        shell=(os.name == "nt")
    )

    print(f"\nAPI: http://127.0.0.1:8000")
    print(f"UI:  http://localhost:5173")
    print("\nPress Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
            # Exit if either process dies
            if be_proc.poll() is not None or fe_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n>> Shutting down...")
    finally:
        # Cleanup
        be_proc.terminate()
        if os.name == "nt":
            # Force kill node process tree on Windows
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(fe_proc.pid)], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            fe_proc.terminate()
        print(">> Done.")

if __name__ == "__main__":
    run()
