import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 获取参数文件路径
    config_file = os.path.join(
        get_package_share_directory('pointcloud_filter'),
        'config',
        'pointcloud_config.yaml'
    )

    return LaunchDescription([
        Node(
            package='pointcloud_filter',
            executable='pointcloud_filter_node',
            name='pointcloud_filter',
            output='screen',
            parameters=[config_file]
        )
    ])