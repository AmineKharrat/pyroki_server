"""Test WebSocket Client

A simple client to test the WebSocket trajectory server by sending trajectory data.
"""

import asyncio
import json
import websockets
import numpy as np


async def send_trajectory():
    """Send a test trajectory to the WebSocket server."""
    
    # Create a simple test trajectory - figure-8 pattern
    num_waypoints = 16
    center = np.array([0.4, 0.0, 0.4])
    scale = 0.2
    
    waypoints = []
    for i in range(num_waypoints):
        t = 2 * np.pi * i / num_waypoints
        
        # Figure-8 parametric equations
        x = center[0] + scale * np.sin(t)
        y = center[1] + scale * np.sin(2 * t) / 2
        z = center[2] + scale * np.cos(t) * 0.2
        
        waypoints.append({
            "position": [x, y, z],
            "orientation": [0, 0, 1, 0],  # wxyz quaternion (pointing down)
            "timestamp": i * 0.8,  # 0.8 second intervals
        })
    
    trajectory_data = {
        "type": "trajectory",
        "waypoints": waypoints,
        "interpolation": "linear",
        "metadata": {
            "total_time": (num_waypoints - 1) * 0.8,
            "description": "Figure-8 test trajectory"
        }
    }
    
    try:
        # Connect to the WebSocket server
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("Connected to WebSocket server")
            
            # Send trajectory data
            await websocket.send(json.dumps(trajectory_data))
            print(f"Sent trajectory with {len(waypoints)} waypoints")
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("No response received (this is normal)")
                
    except ConnectionRefusedError:
        print("Could not connect to WebSocket server. Make sure the server is running!")
    except Exception as e:
        print(f"Error: {e}")


async def send_simple_trajectory():
    """Send a simple straight-line trajectory."""
    
    # Simple straight line trajectory
    start_pos = [0.6, -0.2, 0.3]
    end_pos = [0.6, 0.2, 0.3]
    
    waypoints = [
        {
            "position": start_pos,
            "orientation": [0, 0, 1, 0],
            "timestamp": 0.0,
        },
        {
            "position": end_pos,
            "orientation": [0, 0, 1, 0],
            "timestamp": 2.0,
        }
    ]
    
    trajectory_data = {
        "type": "trajectory",
        "waypoints": waypoints,
        "interpolation": "linear",
        "metadata": {
            "total_time": 2.0,
            "description": "Simple straight-line trajectory"
        }
    }
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("Connected to WebSocket server")
            await websocket.send(json.dumps(trajectory_data))
            print("Sent simple straight-line trajectory")
            
    except ConnectionRefusedError:
        print("Could not connect to WebSocket server. Make sure the server is running!")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main function with menu for different test trajectories."""
    print("WebSocket Trajectory Test Client")
    print("1. Send Figure-8 trajectory")
    print("2. Send simple straight-line trajectory")
    
    choice = input("Choose trajectory (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(send_trajectory())
    elif choice == "2":
        asyncio.run(send_simple_trajectory())
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()