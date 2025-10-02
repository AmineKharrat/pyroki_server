# WebSocket Trajectory Server

A WebSocket server that receives trajectory data and controls a robot using PyRoki. The server listens for trajectory waypoints and moves the robot to follow them in real-time with 3D visualization.

## Files

- `websocket_trajectory_server.py` - Main WebSocket server with robot control
- `test_websocket_client.py` - Test client to send trajectory data

## Features

- **Real-time trajectory execution** - Receives waypoints via WebSocket and executes them
- **3D visualization** - Uses Viser for real-time robot visualization
- **Inverse kinematics** - Automatically computes joint angles from end-effector poses
- **Example trajectories** - Built-in example trajectory generator
- **Interactive GUI** - Web-based controls for testing

## Quick Start

1. **Start the server:**
   ```bash
   conda activate pyrokispace
   python websocket_trajectory_server.py
   ```

2. **Open visualization:** 
   Navigate to http://localhost:8080 in your browser

3. **Test with example trajectory:**
   Click "Send Example Trajectory" in the GUI

4. **Send custom trajectory:**
   ```bash
   # In another terminal
   conda activate pyrokispace
   python test_websocket_client.py
   ```

## WebSocket Message Format

Send JSON messages to `ws://localhost:8765` with this format:

```json
{
  "type": "trajectory",
  "waypoints": [
    {
      "position": [0.5, 0.0, 0.4],
      "orientation": [0, 0, 1, 0],
      "timestamp": 0.0
    },
    {
      "position": [0.6, 0.1, 0.5],
      "orientation": [0, 0, 1, 0],
      "timestamp": 1.0
    }
  ],
  "interpolation": "linear",
  "metadata": {
    "total_time": 1.0,
    "description": "Custom trajectory"
  }
}
```

### Message Fields

- `type`: Must be "trajectory"
- `waypoints`: Array of waypoint objects
  - `position`: [x, y, z] coordinates in meters
  - `orientation`: [w, x, y, z] quaternion (wxyz format)
  - `timestamp`: Time in seconds from trajectory start
- `interpolation`: Type of interpolation between waypoints
- `metadata`: Optional metadata about the trajectory

## Robot Configuration

Currently supports:
- **Panda robot** (default)
- Target link: `panda_hand`

To add other robots, modify the `__init__` method in `TrajectoryWebSocketServer`.

## Integration with External Apps

To connect this with another app that generates trajectories:

1. The external app should connect to `ws://localhost:8765`
2. Send trajectory data in the JSON format above
3. The robot will automatically execute the trajectory with visualization

## Example Trajectories

The server includes several example trajectories:
- **Circular trajectory** - Robot moves in a circle
- **Figure-8 pattern** (test client)
- **Straight line** (test client)

## Technical Details

- **IK solving** - Uses PyRoki's `solve_ik` function
- **Smooth interpolation** - Linear interpolation between waypoints
- **Real-time execution** - Asynchronous trajectory playback
- **Error handling** - Graceful handling of invalid trajectories
- **WebSocket protocol** - Standard WebSocket for communication

## Troubleshooting

- **"websockets not installed"** - Run `pip install websockets` in the pyrokispace environment
- **IK failures** - Check that waypoint positions are reachable by the robot
- **Connection refused** - Make sure the server is running before starting the client
- **Visualization not loading** - Check that port 8080 is available and navigate to http://localhost:8080