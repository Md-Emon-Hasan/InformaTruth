import os, sys, time, subprocess

def start():
    print(">> starting up...")
    
    # setup venv
    if not os.path.exists("venv"):
        print(">> making venv...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])

    python = os.path.join("venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join("venv", "bin", "python")
    npm = "npm.cmd" if os.name == "nt" else "npm"

    # deps
    if os.path.exists("backend/requirements.txt"):
        subprocess.run([python, "-m", "pip", "install", "-q", "-r", "backend/requirements.txt"])
    if not os.path.exists("frontend/node_modules"):
        subprocess.run([npm, "install"], cwd="frontend", shell=(os.name == "nt"))

    # bbe + fe
    be = subprocess.Popen([python, "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"], cwd="backend")
    fe = subprocess.Popen([npm, "run", "dev"], cwd="frontend", shell=(os.name == "nt"))

    print("\nAPI: http://127.0.0.1:8000\nUI:  http://localhost:5173\nCTRL+C to stop.\n")

    try:
        while be.poll() is None and fe.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n>> stopping...")
    finally:
        be.terminate()
        if os.name == "nt":
            subprocess.run(f"taskkill /F /T /PID {fe.pid}", shell=True, capture_output=True)
        else:
            fe.terminate()

if __name__ == "__main__":
    start()
