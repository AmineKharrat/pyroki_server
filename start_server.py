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
    print(f"About to start async server loop...")

    if os.getenv("RAILWAY_ENVIRONMENT"):
        # Railway provides RAILWAY_PUBLIC_DOMAIN or we use the known domain
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN") or os.getenv("RAILWAY_STATIC_URL") or "dependable-happiness-production.up.railway.app"
        print(f"\n{'='*60}")
        print(f"🚀 WebSocket Server Running on Railway")
        print(f"{'='*60}")
        print(f"📡 WebSocket URL: wss://{railway_domain}")
        print(f"🎨 Viser (internal): port {viser_port}")
        print(f"⚡ WebSocket (public): port {port}")
        print(f"{'='*60}\n")
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
        print(f"[MAIN] Calling asyncio.run(server.start_server())...")
        asyncio.run(server.start_server())
        print(f"[MAIN] asyncio.run() returned (this should never happen!)")
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"\n[MAIN] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        print(f"[MAIN] Exiting main()")

if __name__ == "__main__":
    main()