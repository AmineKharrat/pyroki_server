"""Interactive Trajectory Planning

Click to add waypoints, see optimized trajectory with joint movements.
"""

import time
from typing import List, Tuple

import numpy as np
import pyroki as pk
import viser
from robot_descriptions.loaders.yourdfpy import load_robot_description
from viser.extras import ViserUrdf

import pyroki_snippets as pks


class TrajectoryPlanner:
    def __init__(self):
        # Robot setup
        self.urdf = load_robot_description("panda_description")
        self.target_link_name = "panda_hand"
        self.robot = pk.Robot.from_urdf(self.urdf)
        self.robot_coll = pk.collision.RobotCollision.from_urdf(self.urdf)
        
        # Visualization setup
        self.server = viser.ViserServer()
        self.server.scene.add_grid("/ground", width=2, height=2)
        self.urdf_vis = ViserUrdf(self.server, self.urdf, root_node_name="/base")
        
        # Trajectory state
        self.waypoints: List[Tuple[np.ndarray, np.ndarray]] = []  # (position, wxyz)
        self.current_trajectory: np.ndarray = None
        self.waypoint_frames: List = []
        
        # GUI elements
        self.setup_gui()
        
        # Click handler for adding waypoints
        self.server.scene.on_click(self.on_scene_click)
        
    def setup_gui(self):
        """Setup GUI controls."""
        self.clear_button = self.server.gui.add_button("Clear Waypoints")
        self.solve_button = self.server.gui.add_button("Solve Trajectory")
        self.timesteps_slider = self.server.gui.add_slider(
            "Timesteps", min=10, max=50, step=5, initial_value=25
        )
        self.trajectory_slider = self.server.gui.add_slider(
            "Trajectory Step", min=0, max=1, step=1, initial_value=0, disabled=True
        )
        self.playing_checkbox = self.server.gui.add_checkbox("Auto Play", False)
        self.status_text = self.server.gui.add_text("Status", "Click in scene to add waypoints")
        
        # Button callbacks
        self.clear_button.on_click(self.clear_waypoints)
        self.solve_button.on_click(self.solve_trajectory)
        
    def on_scene_click(self, event: viser.ScenePointerEvent):
        """Handle clicks in the 3D scene to add waypoints."""
        if event.event == "click":
            # Use click position, set reasonable height and orientation
            position = np.array([event.ray_origin[0], event.ray_origin[1], 0.4])
            wxyz = np.array([0, 0, 1, 0])  # pointing down for Panda
            
            self.add_waypoint(position, wxyz)
            
    def add_waypoint(self, position: np.ndarray, wxyz: np.ndarray):
        """Add a waypoint to the trajectory."""
        waypoint_idx = len(self.waypoints)
        self.waypoints.append((position.copy(), wxyz.copy()))
        
        # Add visual frame for waypoint
        frame = self.server.scene.add_frame(
            f"/waypoint_{waypoint_idx}",
            position=position,
            wxyz=wxyz,
            axes_length=0.1,
            axes_radius=0.005
        )
        self.waypoint_frames.append(frame)
        
        # Update status
        self.status_text.value = f"Added waypoint {waypoint_idx + 1}. Total: {len(self.waypoints)}"
        
        # Enable solve button if we have at least 2 waypoints
        if len(self.waypoints) >= 2:
            self.solve_button.disabled = False
            
    def clear_waypoints(self):
        """Clear all waypoints."""
        # Remove visual frames
        for frame in self.waypoint_frames:
            frame.remove()
            
        self.waypoints.clear()
        self.waypoint_frames.clear()
        self.current_trajectory = None
        
        # Reset GUI
        self.solve_button.disabled = True
        self.trajectory_slider.disabled = True
        self.trajectory_slider.max = 1
        self.status_text.value = "Waypoints cleared. Click to add new ones."
        
    def solve_trajectory(self):
        """Solve trajectory optimization between waypoints."""
        if len(self.waypoints) < 2:
            self.status_text.value = "Need at least 2 waypoints!"
            return
            
        self.status_text.value = "Solving trajectory..."
        
        try:
            # For simplicity, connect first and last waypoint
            # In practice, you might want to connect all waypoints sequentially
            start_pos, start_wxyz = self.waypoints[0]
            end_pos, end_wxyz = self.waypoints[-1]
            
            # Define obstacles (ground plane)
            ground_coll = pk.collision.HalfSpace.from_point_and_normal(
                np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
            )
            world_coll = [ground_coll]
            
            # Solve trajectory optimization
            traj = pks.solve_trajopt(
                robot=self.robot,
                robot_coll=self.robot_coll,
                world_coll=world_coll,
                target_link_name=self.target_link_name,
                start_position=start_pos,
                start_wxyz=start_wxyz,
                end_position=end_pos,
                end_wxyz=end_wxyz,
                timesteps=self.timesteps_slider.value,
                dt=0.02,
            )
            
            self.current_trajectory = np.array(traj)
            
            # Update trajectory slider
            self.trajectory_slider.max = len(self.current_trajectory) - 1
            self.trajectory_slider.disabled = False
            self.trajectory_slider.value = 0
            
            self.status_text.value = f"Trajectory solved! {len(self.current_trajectory)} timesteps"
            
        except Exception as e:
            self.status_text.value = f"Trajectory solving failed: {str(e)}"
            
    def update_visualization(self):
        """Update robot visualization based on current trajectory step."""
        if self.current_trajectory is not None:
            step = self.trajectory_slider.value
            joint_config = self.current_trajectory[step]
            self.urdf_vis.update_cfg(joint_config)
            
    def run(self):
        """Main loop."""
        while True:
            # Auto-play trajectory
            if (self.playing_checkbox.value and 
                self.current_trajectory is not None and 
                not self.trajectory_slider.disabled):
                
                self.trajectory_slider.value = (
                    (self.trajectory_slider.value + 1) % len(self.current_trajectory)
                )
                
            # Update visualization
            self.update_visualization()
            
            time.sleep(0.1)


def main():
    """Main function."""
    planner = TrajectoryPlanner()
    
    print("🤖 Trajectory Planner Started!")
    print("📝 Instructions:")
    print("   1. Click in the 3D scene to add waypoints")
    print("   2. Click 'Solve Trajectory' when you have 2+ waypoints")
    print("   3. Use the trajectory slider or auto-play to view results")
    print("   4. Visit the web interface to interact")
    
    planner.run()


if __name__ == "__main__":
    main()