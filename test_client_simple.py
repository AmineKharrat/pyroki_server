"""
Simple test client that automatically sends a trajectory to test the server.
"""

import asyncio
import json
import websockets
import numpy as np


async def test_simple_trajectory():
    """Send a simple test trajectory to the server."""
    
    # Simple straight line trajectory
    start_pos = [0.6, -0.1, 0.4]
    end_pos = [0.6, 0.1, 0.4]
    
    waypoints = [
        {
            "position": start_pos,
            "orientation": [0, 0, 1, 0],  # wxyz quaternion
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
            "description": "Simple test trajectory"
        }
    }
    
    try:
        print("Connecting to WebSocket server at ws://localhost:8765...")
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("Connected successfully!")
            
            print("Sending trajectory with 2 waypoints...")
            await websocket.send(json.dumps(trajectory_data))
            print("Trajectory sent!")
            
            # Wait for server response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                if "status" in response_data and response_data["status"] == "success":
                    print(f"✓ Success: {response_data.get('message', 'Trajectory received')}")
                elif "error" in response_data:
                    print(f"✗ Server error: {response_data['error']}")
                else:
                    print(f"Server response: {response}")
                    
            except asyncio.TimeoutError:
                print("No response from server within 5 seconds")
            except json.JSONDecodeError:
                print(f"Non-JSON response from server: {response}")
                
            print("Test completed successfully!")
                
    except ConnectionRefusedError:
        print("ERROR: Could not connect to WebSocket server.")
        print("Make sure the server is running with: python start_server.py")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_simple_trajectory())