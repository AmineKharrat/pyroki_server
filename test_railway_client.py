#!/usr/bin/env python3
"""
Test client for Railway deployment.
Connects to the Railway WebSocket server and receives joint state updates.
"""

import asyncio
import json
import websockets
from datetime import datetime

RAILWAY_URL = "wss://dependable-happiness-production.up.railway.app"


async def test_connection():
    """Connect to Railway server and listen for joint state updates."""

    try:
        print(f"Connecting to Railway server: {RAILWAY_URL}")
        async with websockets.connect(RAILWAY_URL) as websocket:
            print("✓ Connected successfully!")
            print("Listening for joint state updates...")
            print("-" * 60)

            # Listen for messages
            message_count = 0
            async for message in websocket:
                try:
                    data = json.loads(message)

                    if data.get("type") == "joint_state":
                        message_count += 1
                        joint_config = data.get("joint_config", [])
                        timestamp = data.get("timestamp", 0)

                        # Convert timestamp to readable format
                        dt = datetime.fromtimestamp(timestamp)

                        print(f"\n[Message #{message_count}] Received at {dt.strftime('%H:%M:%S.%f')[:-3]}")
                        print(f"Number of joints: {len(joint_config)}")
                        print(f"Joint values:")
                        for i, value in enumerate(joint_config):
                            joint_name = f"Joint {i+1}" if i < 7 else f"Gripper finger {i-6}"
                            print(f"  {joint_name}: {value:8.4f} rad")

                    elif data.get("type") == "robot_status":
                        status = data.get("status")
                        message = data.get("message")
                        print(f"\n🤖 Robot Status: {status}")
                        if message:
                            print(f"   Message: {message}")

                    elif data.get("type") == "pong":
                        print("🏓 Received pong")

                    else:
                        print(f"\nReceived unknown message type: {data.get('type')}")
                        print(json.dumps(data, indent=2))

                    # Stop after 10 messages for testing
                    if message_count >= 10:
                        print("\n" + "-" * 60)
                        print("✓ Test completed! Received 10 joint state updates.")
                        break

                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {message}")
                except Exception as e:
                    print(f"Error processing message: {e}")

    except ConnectionRefusedError:
        print("✗ ERROR: Could not connect to Railway server.")
        print(f"   URL: {RAILWAY_URL}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def send_ping():
    """Send a ping message to test bidirectional communication."""

    try:
        print(f"Connecting to Railway server: {RAILWAY_URL}")
        async with websockets.connect(RAILWAY_URL) as websocket:
            print("✓ Connected successfully!")

            # Send ping
            ping_message = {"type": "ping", "timestamp": datetime.now().timestamp()}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping message")

            # Wait for pong
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)

            if data.get("type") == "pong":
                print("📥 Received pong!")
            else:
                print(f"📥 Received: {data}")

    except asyncio.TimeoutError:
        print("⏱️ No response received (timeout)")
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Main function with menu."""
    print("=" * 60)
    print("Railway WebSocket Test Client")
    print("=" * 60)
    print(f"Server: {RAILWAY_URL}")
    print()
    print("1. Listen for joint state updates (default)")
    print("2. Send ping test")
    print()

    choice = input("Choose option (1 or 2, press Enter for 1): ").strip() or "1"

    if choice == "1":
        asyncio.run(test_connection())
    elif choice == "2":
        asyncio.run(send_ping())
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
