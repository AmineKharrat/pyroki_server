#!/usr/bin/env python3
"""
Send a single target point to the Railway WebSocket server.
"""

import asyncio
import json
import websockets
from datetime import datetime

RAILWAY_URL = "wss://dependable-happiness-production.up.railway.app"


async def send_point(x, y, z, roll=0, pitch=0, yaw=0):
    """Send a single target point to the server.

    Args:
        x, y, z: Position in meters
        roll, pitch, yaw: Orientation in degrees (Euler angles)
    """
    from scipy.spatial.transform import Rotation

    # Convert Euler angles (degrees) to quaternion (wxyz format)
    rotation = Rotation.from_euler('xyz', [roll, pitch, yaw], degrees=True)
    quat_xyzw = rotation.as_quat()  # Returns [x, y, z, w]
    orientation = [quat_xyzw[3], quat_xyzw[0], quat_xyzw[1], quat_xyzw[2]]  # Convert to [w, x, y, z]

    # Create a single-waypoint trajectory
    waypoint = {
        "position": [x, y, z],
        "orientation": orientation,
        "timestamp": 0.0,
    }

    trajectory_data = {
        "type": "trajectory",
        "waypoints": [waypoint],
        "interpolation": "linear",
        "metadata": {
            "total_time": 0.0,
            "description": f"Move to point ({x}, {y}, {z})"
        }
    }

    try:
        print(f"Connecting to Railway server: {RAILWAY_URL}")
        async with websockets.connect(RAILWAY_URL) as websocket:
            print("✓ Connected successfully!")
            print(f"\n📤 Sending target point:")
            print(f"   Position: ({x}, {y}, {z})")
            print(f"   Orientation (Euler): roll={roll}°, pitch={pitch}°, yaw={yaw}°")
            print(f"   Orientation (wxyz quaternion): {orientation}")

            # Send trajectory
            await websocket.send(json.dumps(trajectory_data))
            print("\n✓ Trajectory sent!")

            # Wait for server response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)

                if "status" in data and data["status"] == "success":
                    print(f"\n✓ Server Response: {data.get('message', 'Trajectory received')}")
                    print("   The robot should now move to the target position.")
                elif "error" in data:
                    print(f"\n✗ Server Error: {data['error']}")
                else:
                    print(f"\n📥 Server Response: {response}")

            except asyncio.TimeoutError:
                print("\n⏱️ No immediate response (this is normal)")
                print("   The server is processing the trajectory...")

            # Keep connection open to receive joint state updates
            print("\nListening for joint state updates...")
            print("(Press Ctrl+C to stop)")
            print("-" * 60)

            try:
                async for message in websocket:
                    data = json.loads(message)

                    if data.get("type") == "joint_state":
                        joint_config = data.get("joint_config", [])
                        print(f"Joint state update: {len(joint_config)} joints")

                    elif data.get("type") == "robot_status":
                        status = data.get("status")
                        msg = data.get("message")
                        print(f"🤖 Robot Status: {status} - {msg}")

            except KeyboardInterrupt:
                print("\n\nConnection closed by user.")

    except ConnectionRefusedError:
        print("✗ ERROR: Could not connect to Railway server.")
        print(f"   URL: {RAILWAY_URL}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function to send point (0, 0, 0.5) with no rotation."""
    print("=" * 60)
    print("Send Target Point to Railway Server")
    print("=" * 60)

    # Target point with orientation
    x, y, z = 0.3, 0.3, 0.4 
    roll, pitch, yaw = 0.0, 0.0, 0.0  # No rotation

    print(f"\nTarget Point: ({x}, {y}, {z})")
    print(f"Orientation: roll={roll}°, pitch={pitch}°, yaw={yaw}°")
    print(f"Server: {RAILWAY_URL}")
    print()

    asyncio.run(send_point(x, y, z, roll, pitch, yaw))


if __name__ == "__main__":
    main()
