import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Get the package share directory
    pkg_dir = get_package_share_directory('multi_waypoint_navigator')
    
    # Waypoints configuration file
    waypoints_file = os.path.join(pkg_dir, 'config', 'waypoints.yaml')
    
    return LaunchDescription([
        Node(
            package='multi_waypoint_navigator',
            executable='multi_waypoint_navigator',
            name='multi_waypoint_navigator',
            output='screen',
            parameters=[
                {'waypoints_file': waypoints_file},
                {'position_tolerance': 0.15},
                {'orientation_tolerance': 0.2},
                {'wait_time_at_waypoint': 8.0},  # 设置等待时间为5秒
                {'wait_time_at_homet': 15.0}  # 设置等待时间为5秒
            ]
        )
    ])