#!/usr/bin/env python3
"""
Quick script to verify which robot the server is configured for.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "examples"))

from websocket_trajectory_server import TrajectoryWebSocketServer

def main():
    print("🔍 Checking current server configuration...")
    
    # Create server instance (without starting)
    server = TrajectoryWebSocketServer(robot_name="piper", port=8765)
    
    print(f"✓ Robot name: {server.robot_name}")
    print(f"✓ Target link: {server.target_link_name}")
    print(f"✓ Number of joints: {server.robot.joints.num_actuated_joints}")
    print(f"✓ Default config: {server.current_config[:4]}...")
    
    # Check which URDF was loaded
    joint_names = server.robot.joints.names[:5]
    link_names = server.robot.links.names[:5]
    
    print(f"✓ First 5 joint names: {joint_names}")
    print(f"✓ First 5 link names: {link_names}")
    
    if "panda" in str(joint_names).lower() or "panda" in str(link_names).lower():
        print("❌ ERROR: Server is still using Panda robot!")
        print("This indicates the old server might still be running.")
        return False
    
    if server.target_link_name == "link8" and server.robot_name == "piper":
        print("✅ SUCCESS: Server is correctly configured for Piper robot!")
        return True
    else:
        print(f"❌ ERROR: Unexpected configuration - robot: {server.robot_name}, link: {server.target_link_name}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n💡 SOLUTION: Make sure to completely stop the old server before starting the new one.")
        print("   Try closing all terminal windows running the server and restart.")