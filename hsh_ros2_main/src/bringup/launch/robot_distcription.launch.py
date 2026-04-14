import os
import yaml

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction, TimerAction
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch.conditions import LaunchConfigurationEquals, LaunchConfigurationNotEquals, IfCondition
# ros2 launch rm_nav_bringup bringup_real.launch.py \
#     world:=YOUR_WORLD_NAME \
#     mode:=nav  \
#     lio:=fastlio \
#     lio_rviz:=False \
#     nav_rviz:=True

def generate_launch_description():
    

    ################################ robot_description parameters start ###############################
    launch_params = yaml.safe_load(open(os.path.join(
    get_package_share_directory('bringup'), 'config', 'drivers', 'measurement_params_real.yaml')))

    robot_description = Command(['xacro ', os.path.join(
    get_package_share_directory('bringup'), 'urdf', 'sentry_robot_real.xacro'),
    ' xyz:=', launch_params['base_link2livox_frame']['xyz'], ' rpy:=', launch_params['base_link2livox_frame']['rpy']])
    ################################# robot_description parameters end ################################


    start_robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'use_sim_time': False,
            'robot_description': robot_description
        }],
        output='screen'
    )


    ld = LaunchDescription()


    
    ld.add_action(start_robot_state_publisher_cmd)
    
    
    return ld

