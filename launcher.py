import sys
import time
import subprocess
import urllib.request

print("=" * 70)
print("       BLOODLINE CONNECT -- ONE-CLICK GLOBAL LAUNCHER")
print("=" * 70)
print()

# Step 1: Start backend server
print("[1/3] Starting Flask backend server...")
backend_proc = subprocess.Popen([sys.executable, "backend.py"])

# Step 2: Wait for backend to be ready on port 5000
print("[2/3] Waiting for server to start on http://127.0.0.1:5000 ...")
started = False
for _ in range(15):
    try:
        req = urllib.request.urlopen("http://127.0.0.1:5000/", timeout=2)
        if req.status in (200, 302, 404):
            started = True
            break
    except Exception:
        time.sleep(1)

if not started:
    print("[!] Error: Flask server failed to start on http://127.0.0.1:5000")
    backend_proc.terminate()
    sys.exit(1)

print("[OK] Flask server is active and responding on http://127.0.0.1:5000!")
print()

# Step 3: Launch Global Tunnel
print("[3/3] Launching Secure Global HTTPS Tunnel...")
print("=" * 70)
print(" YOUR WEBSITE IS LIVE GLOBALLY!")
print(" Share the HTTPS URL printed below with anyone around the world:")
print("=" * 70)
print()

tunnel_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:5000", "nokey@localhost.run"]

try:
    tunnel_proc = subprocess.Popen(tunnel_cmd)
    tunnel_proc.wait()
except KeyboardInterrupt:
    print("\nShutting down Bloodline Connect server...")
finally:
    backend_proc.terminate()
    print("Server stopped cleanly.")
