"""Test Streamlit dashboard launch on app.py."""

import subprocess
import time
import urllib.request
import sys
from pathlib import Path

python_exe = Path(__file__).resolve().parent.parent / ".venv" / "Scripts" / "python.exe"

print(f"Testing dashboard startup with: {python_exe} -m streamlit run app.py")
cmd = [
    str(python_exe),
    "-m",
    "streamlit",
    "run",
    "app.py",
    "--server.port",
    "8505",
    "--server.headless",
    "true",
]

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    print("Waiting 6 seconds for Streamlit server to bind...")
    time.sleep(6)
    url = "http://localhost:8505"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            code = response.getcode()
            print(f"SUCCESS! Server responded with HTTP {code}")
    except urllib.error.HTTPError as he:
        print(f"SUCCESS! Streamlit server is active and responded with HTTP {he.code} ({he.reason})")
finally:
    print("Terminating test server...")
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("Test server shutdown successfully.")
