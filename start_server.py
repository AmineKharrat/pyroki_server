#!/usr/bin/env python3
"""
Simple script to start the WebSocket trajectory server.
This helps test the server startup.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "examples"))

from websocket_trajectory_server import TrajectoryWebSocketServer

def main():
    print("Starting WebSocket Trajectory Server...")
    server = TrajectoryWebSocketServer(robot_name="panda", port=8765)
    print("Server initialized successfully!")
    print("Robot configuration loaded.")
    print("Viser visualization should be available at: http://localhost:8080")
    print("WebSocket server will run at: ws://localhost:8765")
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