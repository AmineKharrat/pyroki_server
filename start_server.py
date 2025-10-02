#!/usr/bin/env python3
"""
WebSocket trajectory server for Railway deployment.
Supports both local development and production hosting.
"""

import os
import sys
from pathlib import Path

# Add pyroki source to path for Railway deployment
# The editable install link doesn't survive container layers
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "examples"))

from websocket_trajectory_server import TrajectoryWebSocketServer

def main():
    # Get port from environment variable (Railway) or use default
    port = int(os.getenv("PORT", 8765))
    # Viser visualization port (different from WebSocket port to avoid conflicts)
    viser_port = int(os.getenv("VISER_PORT", 8081))

    # Get host - bind to 0.0.0.0 for Railway, localhost for local dev
    host = "0.0.0.0" if os.getenv("RAILWAY_ENVIRONMENT") else "localhost"

    print("Starting WebSocket Trajectory Server...")
    print(f"Environment: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}")
    print(f"Host: {host}")
    print(f"WebSocket Port: {port}")
    print(f"Viser Port: {viser_port}")

    server = TrajectoryWebSocketServer(robot_name="panda", port=port, host=host, viser_port=viser_port)
    print("Server initialized successfully!")
    print("Robot configuration loaded.")

    if os.getenv("RAILWAY_ENVIRONMENT"):
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-railway-domain.railway.app")
        print(f"\n🚀 WebSocket server running on Railway")
        print(f"📡 WebSocket URL: wss://{railway_domain}")
        print(f"🎨 Viser visualization: https://{railway_domain} (if port {viser_port} is exposed)")
        print(f"\nNote: Railway only exposes port {port} by default.")
        print(f"Viser runs on port {viser_port} for internal use.")
    else:
        print("Viser visualization should be available at: http://localhost:{viser_port}")
        print(f"WebSocket server will run at: ws://{host}:{port}")
        print("\nYou can:")
        print("1. Open http://localhost:{viser_port} in your browser to see the robot")
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