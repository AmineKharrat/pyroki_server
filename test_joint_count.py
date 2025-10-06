#!/usr/bin/env python3
"""Test script to show exactly how many joints PyRoki extracts from Panda URDF."""

import pyroki as pk
from robot_descriptions.loaders.yourdfpy import load_robot_description

# Load the same URDF that the server uses
print("Loading Panda URDF...")
urdf = load_robot_description("panda_description")

# Create robot the same way the server does
print("Creating PyRoki robot...")
robot = pk.Robot.from_urdf(urdf)

# Get default configuration the same way the server does
print("\n" + "="*60)
print("ROBOT CONFIGURATION:")
print("="*60)

default_config = robot.joint_var_cls.default_factory()
print(f"Number of joints: {len(default_config)}")
print(f"Joint configuration type: {type(default_config)}")
print(f"Joint values: {default_config}")
print(f"\n")

# Show joint names
print("="*60)
print("JOINT NAMES:")
print("="*60)
print(f"Joint names: {robot.links.names}")
print(f"\n")

# Show what gets sent via tolist()
import numpy as np
config_np = np.array(default_config)
joint_list = config_np.tolist()
print("="*60)
print("WHAT GETS BROADCAST:")
print("="*60)
print(f"Number of values in broadcast: {len(joint_list)}")
print(f"Broadcast values: {joint_list}")
