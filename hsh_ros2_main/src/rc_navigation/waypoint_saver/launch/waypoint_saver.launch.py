import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Get the package share directory
    pkg_dir = get_package_share_directory('waypoint_saver')
    
    # # Waypoints configuration file
    # waypoints_file = os.path.join(pkg_dir, 'config', 'waypoints.yaml')
    
    return LaunchDescription([
        Node(
            package='waypoint_saver',
            executable='waypoint_saver',
            name='waypoint_saver',
            output='screen',
            parameters=[
                {'save_path': '/home/r2/Desktop/hsh_ros2_main/src/rc_navigation/multi_waypoint_navigator/config/waypoints.yaml'},
                {'min_record_distance': 0.2},

            ]
        )
    ])