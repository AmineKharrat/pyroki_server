#!/usr/bin/env python3
"""
WebSocket trajectory server for Railway deployment.
Supports both local development and production hosting.
"""

import os
import sys
from pathlib import Path

# Debug: Print Python path and sys.path
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path}")

# Debug: Check if pyroki source exists
import os
print(f"\nChecking for pyroki source:")
print(f"/app exists: {os.path.exists('/app')}")
print(f"/app/src exists: {os.path.exists('/app/src')}")
print(f"/app/src/pyroki exists: {os.path.exists('/app/src/pyroki')}")
print(f"/app contents: {os.listdir('/app')}")
if os.path.exists('/app/src'):
    print(f"/app/src contents: {os.listdir('/app/src')}")

# Debug: Check what's in site-packages
import site
site_packages = site.getsitepackages()[0]
print(f"\nsite-packages: {site_packages}")
if os.path.exists(site_packages):
    print(f"pyroki in site-packages: {'pyroki' in os.listdir(site_packages)}")
    print(f"pyroki.egg-link exists: {os.path.exists(os.path.join(site_packages, 'pyroki.egg-link'))}")
    if os.path.exists(os.path.join(site_packages, 'pyroki.egg-link')):
        with open(os.path.join(site_packages, 'pyroki.egg-link')) as f:
            print(f"pyroki.egg-link content: {f.read()}")

sys.path.insert(0, str(Path(__file__).parent / "examples"))

from websocket_trajectory_server import TrajectoryWebSocketServer

def main():
    # Get port from environment variable (Railway) or use default
    port = int(os.getenv("PORT", 8765))

    # Get host - bind to 0.0.0.0 for Railway, localhost for local dev
    host = "0.0.0.0" if os.getenv("RAILWAY_ENVIRONMENT") else "localhost"

    print("Starting WebSocket Trajectory Server...")
    print(f"Environment: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}")
    print(f"Host: {host}")
    print(f"Port: {port}")

    server = TrajectoryWebSocketServer(robot_name="panda", port=port, host=host)
    print("Server initialized successfully!")
    print("Robot configuration loaded.")

    if os.getenv("RAILWAY_ENVIRONMENT"):
        print(f"WebSocket server running on Railway")
        print(f"Connect clients to: wss://your-railway-domain.railway.app")
    else:
        print("Viser visualization should be available at: http://localhost:8080")
        print(f"WebSocket server will run at: ws://{host}:{port}")
        print("\nYou can:")
        print("1. Open http://localhost:8080 in your browser to see the robot")
        print("2. Click 'Send Example Trajectory' to test trajectory execution")
        print("3. Click 'Reset Robot Pose' to return to initial configuration")
        print("4. Run python test_websocket_client.py to send custom trajectories")

    print("\nPress Ctrl+C to stop the server")

    try:
        import asyncio
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\nServer stopped by user")

if __name__ == "__main__":
    main()