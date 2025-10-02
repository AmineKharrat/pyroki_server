"""WebSocket Trajectory Server

A WebSocket server that receives trajectory data and controls a robot using PyRoki.
The server listens for trajectory waypoints and moves the robot to follow them in real-time.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pyroki as pk
import viser
import websockets
from robot_descriptions.loaders.yourdfpy import load_robot_description
from viser.extras import ViserUrdf

# Add the examples directory to the Python path to import pyroki_snippets
examples_dir = Path(__file__).parent / "examples"
sys.path.insert(0, str(examples_dir))

import pyroki_snippets as pks


class TrajectoryWebSocketServer:
    """WebSocket server for receiving and executing robot trajectories."""

    def __init__(self, robot_name: str = "panda", port: int = 8765, host: str = "localhost", viser_port: int = 8081):
        self.port = port
        self.host = host
        self.robot_name = robot_name

        # Robot setup
        if robot_name == "panda":
            self.urdf = load_robot_description("panda_description")
            self.target_link_name = "panda_hand"
        elif robot_name == "piper":
            self.urdf = load_robot_description("piper_description")
            self.target_link_name = "link8"  # Use the last link as end-effector
        else:
            raise ValueError(f"Unsupported robot: {robot_name}")

        self.robot = pk.Robot.from_urdf(self.urdf)

        # Apply -90 degree rotation around X-axis to robot base
        self._apply_base_transform()

        # Visualization setup - use separate port to avoid conflicts
        self.server = viser.ViserServer(port=viser_port)
        self.server.scene.add_grid("/ground", width=2, height=2)
        
        # Create ViserUrdf with the robot
        self.urdf_vis = ViserUrdf(self.server, self.urdf, root_node_name="/robot")
        
        # Trajectory state
        self.current_trajectory: List[Dict[str, Any]] = []
        self.current_waypoint_index = 0
        self.is_executing = False
        
        # WebSocket clients for broadcasting joint states
        self.connected_clients: set = set()
        
        # Initialize robot in a reasonable configuration
        self.current_config = self._get_initial_config()
        
        # Add GUI controls
        self._setup_gui()
        
        # Set initial robot pose
        print(f"Setting initial robot configuration: {self.current_config}")
        print(f"Config type: {type(self.current_config)}")
        
        # Convert to the same format that solve_ik returns (numpy array)
        config_np = np.array(self.current_config)
        print(f"Converted config type: {type(config_np)}")
        self.urdf_vis.update_cfg(config_np)
        
        # Store as numpy array for consistency
        self.current_config = config_np
        
    def _apply_base_transform(self):
        """Apply -90 degree rotation around X-axis to robot base frame."""
        import jax.numpy as jnp
        from scipy.spatial.transform import Rotation
        
        # Create -90 degree rotation around X-axis
        rotation_matrix = Rotation.from_euler('x', -90, degrees=True).as_matrix()
        
        # Store the base transformation matrix for use in kinematics
        self.base_transform = jnp.eye(4)
        self.base_transform = self.base_transform.at[:3, :3].set(rotation_matrix)
        
        # Store the inverse transform for converting back
        self.base_transform_inv = jnp.linalg.inv(self.base_transform)
        
    def _transform_target_pose(self, position, orientation_wxyz):
        """Transform target pose from world frame to robot's base frame."""
        import jax.numpy as jnp
        from scipy.spatial.transform import Rotation
        
        # Convert position to homogeneous coordinates
        pos_homo = jnp.array([position[0], position[1], position[2], 1.0])
        
        # Transform position
        transformed_pos = self.base_transform_inv @ pos_homo
        
        # Convert quaternion to rotation matrix
        quat_xyzw = [orientation_wxyz[1], orientation_wxyz[2], orientation_wxyz[3], orientation_wxyz[0]]
        ori_matrix = Rotation.from_quat(quat_xyzw).as_matrix()
        
        # Transform orientation
        transformed_ori_matrix = self.base_transform_inv[:3, :3] @ ori_matrix
        
        # Convert back to quaternion (wxyz format)
        transformed_quat_xyzw = Rotation.from_matrix(transformed_ori_matrix).as_quat()
        transformed_quat_wxyz = [transformed_quat_xyzw[3], transformed_quat_xyzw[0], 
                                transformed_quat_xyzw[1], transformed_quat_xyzw[2]]
        
        return jnp.concatenate([transformed_pos[:3], jnp.array(transformed_quat_wxyz)])
        
        
    def _get_initial_config(self) -> np.ndarray:
        """Get a reasonable initial configuration for the robot."""
        if self.robot_name == "panda":
            # Use the robot's default configuration which is already reasonable for Panda
            default_config = self.robot.joint_var_cls.default_factory()
            print(f"Using default config with {len(default_config)} joints: {default_config}")
            return default_config
        elif self.robot_name == "piper":
            # Use the robot's default configuration for Piper
            default_config = self.robot.joint_var_cls.default_factory()
            print(f"Using default config with {len(default_config)} joints: {default_config}")
            return default_config
        else:
            # Default to all zeros for unknown robots
            return self.robot.joint_var_cls.default_factory()
    
    def _setup_gui(self):
        """Set up the GUI controls for the visualizer."""
        self.status_handle = self.server.gui.add_text("Status", "Waiting for trajectory...")
        self.waypoint_handle = self.server.gui.add_number("Current Waypoint", 0, disabled=True)
        self.total_waypoints_handle = self.server.gui.add_number("Total Waypoints", 0, disabled=True)
        
        # Add example trajectory button
        example_button = self.server.gui.add_button("Send Example Trajectory")
        example_button.on_click(self._handle_example_trajectory_click)
        
        # Add reset robot button
        reset_button = self.server.gui.add_button("Reset Robot Pose")
        reset_button.on_click(lambda _: self._reset_robot_pose())
        
        # Store the main event loop for button callbacks
        self.main_loop = None
        
    def _handle_example_trajectory_click(self, _):
        """Handle example trajectory button click from GUI thread."""
        if self.main_loop is not None:
            # Schedule the coroutine in the main event loop
            asyncio.run_coroutine_threadsafe(
                self._send_example_trajectory(), 
                self.main_loop
            )
        else:
            print("Event loop not available, cannot send example trajectory")
    
    def _reset_robot_pose(self):
        """Reset robot to initial pose."""
        self.current_config = self._get_initial_config()
        config_np = np.array(self.current_config)
        self.urdf_vis.update_cfg(config_np)
        self.status_handle.value = "Robot reset to initial pose"
        
        # Broadcast the reset joint state to webapp
        asyncio.create_task(self._broadcast_joint_state(config_np))
        
    async def _broadcast_joint_state(self, joint_config: np.ndarray):
        """Broadcast current joint state to all connected WebSocket clients."""
        if not self.connected_clients:
            return
            
        message = {
            "type": "joint_state",
            "joint_config": joint_config.tolist(),
            "timestamp": time.time()
        }
        
        # Send to all connected clients (create copy to avoid iteration issues)
        disconnected_clients = set()
        for client in self.connected_clients.copy():
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients
        
    async def _broadcast_robot_status(self, status: str, message: str = ""):
        """Broadcast robot status to all connected WebSocket clients."""
        if not self.connected_clients:
            return
            
        status_message = {
            "type": "robot_status",
            "status": status,
            "message": message,
            "timestamp": time.time()
        }
        
        # Send to all connected clients (create copy to avoid iteration issues)
        disconnected_clients = set()
        for client in self.connected_clients.copy():
            try:
                await client.send(json.dumps(status_message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                print(f"Error broadcasting status to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients
        
    async def _send_example_trajectory(self):
        """Send an example trajectory for testing."""
        example_trajectory = self._generate_example_trajectory()
        await self._process_trajectory(example_trajectory)
        
    def _generate_example_trajectory(self) -> Dict[str, Any]:
        """Generate an example trajectory for testing."""
        # Get current end-effector position as center
        current_fk = self.robot.forward_kinematics(self.current_config)
        target_link_index = self.robot.links.names.index(self.target_link_name)
        # FK returns SE3 poses in 7D format: [qw, qx, qy, qz, tx, ty, tz]
        current_pose = current_fk[target_link_index]
        current_pos = current_pose[4:7]  # Extract translation part
        
        print(f"Current end-effector position: {current_pos}")
        
        # Create a simple circular trajectory around current position
        num_waypoints = 16
        center = current_pos.copy()
        # Ensure center is at a reasonable height
        center[2] = max(center[2], 0.3)
        radius = 0.1
        
        waypoints = []
        for i in range(num_waypoints):
            angle = 2 * np.pi * i / num_waypoints
            position = center + radius * np.array([np.cos(angle), np.sin(angle), 0.05 * np.sin(2 * angle)])
            
            waypoints.append({
                "position": position.tolist(),
                "orientation": [0, 0, 1, 0],  # wxyz quaternion (pointing down)
                "timestamp": i * 0.3,  # 0.3 second intervals
                "joint_config": None  # Will be computed via IK
            })
            
        return {
            "type": "trajectory",
            "waypoints": waypoints,
            "interpolation": "linear",
            "metadata": {
                "total_time": (num_waypoints - 1) * 0.3,
                "description": "Example circular trajectory around current position"
            }
        }
        
    async def _process_trajectory(self, trajectory_data: Dict[str, Any]):
        """Process received trajectory data and start execution."""
        try:
            if trajectory_data.get("type") != "trajectory":
                error_msg = f"Unknown message type: {trajectory_data.get('type')}"
                print(error_msg)
                raise ValueError(error_msg)
                
            waypoints = trajectory_data.get("waypoints", [])
            if not waypoints:
                error_msg = "No waypoints in trajectory"
                print(error_msg)
                raise ValueError(error_msg)
                
            print(f"Received trajectory with {len(waypoints)} waypoints")
            
            # Compute joint configurations for each waypoint via IK
            processed_waypoints = []
            for i, waypoint in enumerate(waypoints):
                try:
                    position = np.array(waypoint["position"])
                    orientation = np.array(waypoint["orientation"])  # wxyz
                    
                    print(f"Processing waypoint {i+1}: pos={position}, ori={orientation}")
                    
                    # Transform target position/orientation to robot's base frame
                    target_pose_transformed = self._transform_target_pose(position, orientation)
                    
                    # Solve IK for this waypoint
                    joint_config = pks.solve_ik(
                        robot=self.robot,
                        target_link_name=self.target_link_name,
                        target_position=target_pose_transformed[:3],
                        target_wxyz=target_pose_transformed[3:],
                    )
                    
                    waypoint["joint_config"] = joint_config
                    processed_waypoints.append(waypoint)
                    print(f"✓ Waypoint {i+1} IK solved: {joint_config[:3]}...")
                    
                except Exception as e:
                    print(f"✗ IK failed for waypoint {i+1} {waypoint}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                    
            if not processed_waypoints:
                error_msg = "No valid waypoints after IK processing"
                print(error_msg)
                raise ValueError(error_msg)
                
            print(f"Successfully processed {len(processed_waypoints)} waypoints")
            
            # Store trajectory and start execution
            self.current_trajectory = processed_waypoints
            self.current_waypoint_index = 0
            self.total_waypoints_handle.value = len(processed_waypoints)
            
            # Start trajectory execution
            asyncio.create_task(self._execute_trajectory())
            print("Trajectory execution started")
            
        except Exception as e:
            print(f"Error in _process_trajectory: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to be caught by websocket handler
        
    async def _execute_trajectory(self):
        """Execute the current trajectory."""
        if not self.current_trajectory or self.is_executing:
            return
            
        self.is_executing = True
        self.status_handle.value = "Executing trajectory..."
        
        # Broadcast start of trajectory execution
        await self._broadcast_robot_status("executing", "Starting trajectory execution")
        
        try:
            start_time = time.time()
            
            for i, waypoint in enumerate(self.current_trajectory):
                self.current_waypoint_index = i
                self.waypoint_handle.value = i + 1
                
                # Get target joint configuration
                target_config = waypoint["joint_config"]
                target_config_np = np.array(target_config)  # Convert JAX array to numpy
                
                # Simple interpolation to target (could be made smoother)
                steps = 20
                for step in range(steps):
                    alpha = (step + 1) / steps
                    interpolated_config = (1 - alpha) * self.current_config + alpha * target_config_np
                    
                    # Update visualization (make sure it's numpy array)
                    config_for_vis = np.array(interpolated_config)
                    self.urdf_vis.update_cfg(config_for_vis)
                    
                    # Broadcast joint state to webapp
                    await self._broadcast_joint_state(config_for_vis)
                    
                    # Debug: print current config occasionally
                    if step % 10 == 0:
                        print(f"Step {step}: joints = {interpolated_config[:3]}...")
                    
                    # Small delay for smooth motion
                    await asyncio.sleep(0.05)
                    
                self.current_config = target_config_np
                
                # Wait until the waypoint timestamp if specified
                if "timestamp" in waypoint:
                    target_time = start_time + waypoint["timestamp"]
                    current_time = time.time()
                    if current_time < target_time:
                        await asyncio.sleep(target_time - current_time)
                        
        except Exception as e:
            print(f"Error executing trajectory: {e}")
            
        finally:
            self.is_executing = False
            self.status_handle.value = "Trajectory completed"
            
            # Broadcast completion status
            await self._broadcast_robot_status("idle", "Trajectory execution completed")
            
    async def handle_websocket(self, websocket):
        """Handle incoming WebSocket connections."""
        print(f"Client connected from {websocket.remote_address}")
        
        # Add client to connected clients set
        self.connected_clients.add(websocket)
        
        # Send initial robot status
        await self._broadcast_robot_status("idle", "Robot ready")
        
        # Send current joint state
        await self._broadcast_joint_state(np.array(self.current_config))
        
        try:
            async for message in websocket:
                print(f"Received message: {message[:100]}...")  # Print first 100 chars
                try:
                    data = json.loads(message)
                    
                    # Handle ping messages for heartbeat
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": time.time()
                        }))
                        continue
                    
                    print(f"Processing trajectory with {len(data.get('waypoints', []))} waypoints")
                    await self._process_trajectory(data)
                    
                    # Send success response
                    await websocket.send(json.dumps({
                        "status": "success",
                        "message": "Trajectory received and processing started"
                    }))
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON received: {e}"
                    print(error_msg)
                    await websocket.send(json.dumps({
                        "error": error_msg
                    }))
                except Exception as e:
                    error_msg = f"Error processing message: {e}"
                    print(error_msg)
                    print(f"Exception type: {type(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    await websocket.send(json.dumps({
                        "error": error_msg,
                        "type": str(type(e))
                    }))
                    
        except websockets.exceptions.ConnectionClosedOK:
            print("Client disconnected normally")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Client disconnected with error: {e}")
        except Exception as e:
            print(f"WebSocket error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Remove client from connected clients set
            self.connected_clients.discard(websocket)
            print(f"Client removed. {len(self.connected_clients)} clients remaining.")
            
    async def start_server(self):
        """Start the WebSocket server."""
        # Store reference to the main event loop
        self.main_loop = asyncio.get_running_loop()
        
        print(f"Starting WebSocket server on port {self.port}")
        print("Viser visualization available at: http://localhost:8080")
        
        # Start WebSocket server
        server = await websockets.serve(
            self.handle_websocket,
            self.host,
            self.port
        )
        
        print(f"WebSocket server running at ws://localhost:{self.port}")
        print("Send trajectory data or click 'Send Example Trajectory' in the GUI")
        
        # Keep server running
        await server.wait_closed()
        

def main():
    """Main function to run the WebSocket trajectory server."""
    server = TrajectoryWebSocketServer(robot_name="panda", port=8765)
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("Server stopped by user")


if __name__ == "__main__":
    main()