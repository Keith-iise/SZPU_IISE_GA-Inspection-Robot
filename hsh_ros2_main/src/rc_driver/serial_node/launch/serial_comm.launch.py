from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import PushRosNamespace
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    package_name = 'serial_node'

    package_dir = get_package_share_directory(package_name)
    parames_file = PathJoinSubstitution([
        package_dir,
        'config',
        'serial_configs.yaml'
    ])

    

    return LaunchDescription([
        Node(
            package=package_name,
            executable='serial_twist_publisher',
            name='serial_twist_publisher',
            parameters=[parames_file],
            output='screen'
        )
    ])







# from launch import LaunchDescription
# from launch_ros.actions import Node

# def generate_launch_description():
#     return LaunchDescription([
#         Node(
#             package='serial_node',
#             executable='serial_twist_publisher',
#             name='serial_twist_publisher',
#             parameters=[
#                 {'port': '/dev/ttyUSB0'},
#                 {'baudrate': 115200},
#                 {'linear_scale': 4000.0},     # m/s to mm/s
#                 {'angular_scale': 400.0},   # rad/s to deg/s (1 rad ≈ 57.2958 deg)
#             ],
#             output='screen'
#         )
#     ])