#!/usr/bin/env python3
"""
Test script to verify the WebSocket trajectory server initialization.
Run this separately to test if the server setup is working correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "examples"))

def test_imports():
    """Test all required imports."""
    print("Testing imports...")
    try:
        import asyncio
        import json
        import time
        from typing import Any, Dict, List, Optional
        import numpy as np
        import pyroki as pk
        import viser
        import websockets
        from robot_descriptions.loaders.yourdfpy import load_robot_description
        from viser.extras import ViserUrdf
        import pyroki_snippets as pks
        print("✓ All imports successful!")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_robot_setup():
    """Test robot loading and configuration."""
    print("Testing robot setup...")
    try:
        import numpy as np
        import pyroki as pk
        from robot_descriptions.loaders.yourdfpy import load_robot_description
        
        # Load robot
        urdf = load_robot_description("panda_description")
        robot = pk.Robot.from_urdf(urdf)
        
        print(f"✓ Robot loaded with {robot.joints.num_actuated_joints} joints")
        
        # Test configuration
        default_config = robot.joint_var_cls.default_factory()
        config_np = np.array(default_config)
        print(f"✓ Configuration created: {config_np[:3]}...")
        
        # Test forward kinematics
        fk = robot.forward_kinematics(config_np)
        target_link_index = robot.links.names.index('panda_hand')
        current_pose = fk[target_link_index]
        current_pos = current_pose[4:7]
        print(f"✓ Forward kinematics: end-effector at {current_pos}")
        
        return True, robot, urdf, config_np
    except Exception as e:
        print(f"✗ Robot setup failed: {e}")
        return False, None, None, None

def test_visualization_setup(urdf, config_np):
    """Test visualization setup (non-blocking)."""
    print("Testing visualization setup...")
    try:
        import viser
        from viser.extras import ViserUrdf
        
        # Create server
        server = viser.ViserServer(port=8084)  # Use different port to avoid conflicts
        print(f"✓ Viser server created on port 8084")
        
        # Create URDF visualization
        urdf_vis = ViserUrdf(server, urdf, root_node_name="/test_robot")
        print("✓ URDF visualization created")
        
        # Test configuration update
        urdf_vis.update_cfg(config_np)
        print("✓ Robot configuration updated successfully")
        print(f"✓ Visualization available at: http://localhost:8084")
        
        return True, server, urdf_vis
    except Exception as e:
        print(f"✗ Visualization setup failed: {e}")
        return False, None, None

def test_ik_functionality():
    """Test inverse kinematics."""
    print("Testing IK functionality...")
    try:
        import numpy as np
        import pyroki as pk
        import pyroki_snippets as pks
        from robot_descriptions.loaders.yourdfpy import load_robot_description
        
        urdf = load_robot_description("panda_description")
        robot = pk.Robot.from_urdf(urdf)
        
        # Test IK
        target_position = np.array([0.5, 0.0, 0.4])
        target_wxyz = np.array([0, 0, 1, 0])
        
        config = pks.solve_ik(robot, 'panda_hand', target_wxyz, target_position)
        print(f"✓ IK solution computed: {config[:3]}...")
        
        return True, config
    except Exception as e:
        print(f"✗ IK test failed: {e}")
        return False, None

def main():
    """Run all tests."""
    print("=" * 50)
    print("WebSocket Trajectory Server - Component Tests")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        return False
    print()
    
    # Test robot setup
    robot_ok, robot, urdf, config_np = test_robot_setup()
    if not robot_ok:
        return False
    print()
    
    # Test IK
    ik_ok, ik_config = test_ik_functionality()
    if not ik_ok:
        return False
    print()
    
    # Test visualization (this will create a server on port 8084)
    viz_ok, server, urdf_vis = test_visualization_setup(urdf, config_np)
    if not viz_ok:
        return False
    print()
    
    print("=" * 50)
    print("✓ ALL TESTS PASSED!")
    print("=" * 50)
    print()
    print("The WebSocket trajectory server should work correctly.")
    print("You can now run:")
    print("  python websocket_trajectory_server.py")
    print()
    print("Or use the convenience script:")
    print("  python start_server.py")
    print()
    print(f"Test visualization is running at: http://localhost:8084")
    print("Press Ctrl+C to stop the test server")
    
    # Keep the test visualization running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTest server stopped")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)