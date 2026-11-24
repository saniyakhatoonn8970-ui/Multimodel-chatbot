import sys
import subprocess
import os
import time
import socket

def free_port_if_occupied(port):
    """If a leftover zombie process is occupying the port, terminate it."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) == 0:
                out = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
                for line in out.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 5 and "LISTENING" in parts:
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) != os.getpid():
                            subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
    except Exception:
        pass

def print_help():
    print("""
======================================================
  MindBridge AI Developer Launcher
======================================================
Usage:
  python scripts/run_dev.py          - Start BOTH Backend & Frontend together
  python scripts/run_dev.py backend  - Start only FastAPI backend (port 8000)
  python scripts/run_dev.py frontend - Start only Streamlit frontend (port 8501)
  python scripts/run_dev.py test     - Run automated test suite
  python scripts/run_dev.py check    - Run configuration diagnostics
""")

def run_both():
    print("=" * 60)
    print(" Starting MindBridge AI (Backend + Frontend)...")
    print("=" * 60)

    # Clean up any leftover ports from prior runs
    free_port_if_occupied(8000)
    free_port_if_occupied(8501)
    time.sleep(0.5)

    # 1. Start FastAPI Backend process
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    backend_proc = subprocess.Popen(backend_cmd)

    # Wait for backend to initialize
    time.sleep(2.0)

    # 2. Start Streamlit Frontend process
    frontend_cmd = [sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py", "--server.port", "8501"]
    frontend_proc = subprocess.Popen(frontend_cmd)

    print("\n" + "=" * 60)
    print("  MindBridge AI is LIVE!")
    print("  - Web Chat Interface: http://localhost:8501")
    print("  - Backend API:        http://127.0.0.1:8000")
    print("  - Interactive Docs:   http://127.0.0.1:8000/docs")
    print("=" * 60)
    print("  Open http://localhost:8501 in your browser.")
    print("  Press Ctrl+C in this terminal to stop both servers.\n")

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\nStopping MindBridge AI servers...")
    finally:
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=2)
        except Exception:
            backend_proc.kill()
        try:
            frontend_proc.terminate()
            frontend_proc.wait(timeout=2)
        except Exception:
            frontend_proc.kill()
        print("[Servers stopped cleanly]")

def run():
    if len(sys.argv) < 2 or sys.argv[1].lower() in ("all", "start"):
        run_both()
        return

    cmd = sys.argv[1].lower()
    if cmd == "backend":
        free_port_if_occupied(8000)
        subprocess.run([sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"])
    elif cmd == "frontend":
        free_port_if_occupied(8501)
        subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py", "--server.port", "8501"])
    elif cmd == "test":
        subprocess.run([sys.executable, "-m", "pytest", "backend/tests", "-v"])
    elif cmd == "check":
        subprocess.run([sys.executable, "scripts/check_config.py"])
    else:
        print(f"Unknown command: {cmd}")
        print_help()

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[Stopped by user]")
        sys.exit(0)
