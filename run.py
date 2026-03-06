#!/usr/bin/env python3
"""
SensorWatch — one-command local startup.

Usage:
    python run.py          # starts backend on :8000, frontend on :3000
    python run.py --backend-only   # starts only the backend

Requires: Python 3.10+, Node.js 18+ (for frontend)
"""

import argparse
import os
import subprocess
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")


def run(cmd, cwd=None, check=True):
    print(f"  > {cmd}")
    return subprocess.run(cmd, shell=True, cwd=cwd, check=check)


def start_backend_only():
    print("\n[1/2] Installing Python dependencies …")
    run(f"{sys.executable} -m pip install -r requirements.txt -q", cwd=BACKEND)

    print("\n[2/2] Starting SensorWatch backend on http://localhost:8000 …\n")
    os.chdir(BACKEND)
    os.execvp(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    )


def start_full():
    print("\n[1/4] Installing Python dependencies …")
    run(f"{sys.executable} -m pip install -r requirements.txt -q", cwd=BACKEND)

    has_node = shutil.which("node") is not None
    if not has_node:
        print("\n⚠  Node.js not found. Starting backend only.")
        print("   Install Node.js 18+ and run 'cd frontend && npm install && npm run dev' separately.\n")
        start_backend_only()
        return

    print("\n[2/4] Installing frontend dependencies …")
    run("npm install", cwd=FRONTEND)

    print("\n[3/4] Building frontend …")
    run("npm run build", cwd=FRONTEND)

    print("\n[4/4] Starting SensorWatch on http://localhost:8000 …")
    print("       (Frontend served from built assets)\n")
    os.chdir(BACKEND)
    os.execvp(
        sys.executable,
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SensorWatch launcher")
    parser.add_argument("--backend-only", action="store_true", help="Start only the API server")
    args = parser.parse_args()

    if args.backend_only:
        start_backend_only()
    else:
        start_full()
