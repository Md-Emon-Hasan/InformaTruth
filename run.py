import os, sys, time, subprocess, threading, webbrowser, signal
from contextlib import contextmanager

def run_checked(cmd, **kwargs):
    """Run a command and abort with a clear message if it fails."""
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"\n>> command failed (exit {result.returncode}): {cmd}")
        sys.exit(result.returncode)
    return result

@contextmanager
def ignore_interrupts():

    previous = None
    try:
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    except (ValueError, OSError):
        pass  # e.g. not on the main thread — nothing to shield
    try:
        yield
    finally:
        if previous is not None:
            signal.signal(signal.SIGINT, previous)

def start():
    print(">> starting up...")

    # ---- setup: shielded from stray Ctrl+C so a long install can't be aborted ----
    with ignore_interrupts():
        # setup venv
        if not os.path.exists("venv"):
            print(">> making venv...")
            run_checked([sys.executable, "-m", "venv", "venv"])

        python = os.path.join("venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join("venv", "bin", "python")
        npm = "npm.cmd" if os.name == "nt" else "npm"

        # make sure pip exists inside the venv (some venvs get created without it)
        if subprocess.run([python, "-m", "pip", "--version"], capture_output=True).returncode != 0:
            print(">> bootstrapping pip...")
            run_checked([python, "-m", "ensurepip", "--upgrade"])

        # deps — only install once; a marker file lets later runs skip the slow step
        deps_marker = os.path.join("venv", ".deps_installed")
        if os.path.exists("backend/requirements.txt") and not os.path.exists(deps_marker):
            print(">> installing backend deps (first run only, this can take several minutes)...")
            # no -q: show pip progress so it doesn't look frozen while torch/transformers download.
            # On Windows, run pip in its own process group so an inherited Ctrl+C / console signal
            # can't kill it mid-download ("Operation cancelled by user").
            pip_kwargs = {}
            if os.name == "nt":
                pip_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            run_checked([python, "-m", "pip", "install", "-r", "backend/requirements.txt"], **pip_kwargs)
            with open(deps_marker, "w") as f:
                f.write("ok")
        else:
            print(">> backend deps already installed, skipping.")
        if not os.path.exists("frontend/node_modules"):
            print(">> installing frontend deps...")
            run_checked([npm, "install"], cwd="frontend", shell=(os.name == "nt"))

    # be + fe — give each server its own process group so a stray console signal
    # (e.g. VSCode auto-activating the venv in the terminal) can't tear them down.
    # We shut them down explicitly in the finally block instead.
    proc_kwargs = {}
    if os.name == "nt":
        proc_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    be = subprocess.Popen([python, "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"], cwd="backend", **proc_kwargs)
    fe = subprocess.Popen([npm, "run", "dev"], cwd="frontend", shell=(os.name == "nt"), **proc_kwargs)

    ui_url = "http://localhost:5173"
    print(f"\nAPI: http://127.0.0.1:8000\nUI:  {ui_url}\nCTRL+C to stop.\n")

    # open the UI in the browser once the dev server has had a moment to boot
    def open_browser():
        time.sleep(3)
        if fe.poll() is None:
            print(f">> opening {ui_url} in browser...")
            webbrowser.open(ui_url)

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        while True:
            if be.poll() is not None:
                print(f"\n>> backend exited (code {be.returncode}). shutting down frontend too.")
                break
            if fe.poll() is not None:
                print(f"\n>> frontend exited (code {fe.returncode}). shutting down backend too.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n>> stopping...")
    finally:
        if be.poll() is None:
            be.terminate()
        if fe.poll() is None:
            if os.name == "nt":
                subprocess.run(f"taskkill /F /T /PID {fe.pid}", shell=True, capture_output=True)
            else:
                fe.terminate()

if __name__ == "__main__":
    start()
