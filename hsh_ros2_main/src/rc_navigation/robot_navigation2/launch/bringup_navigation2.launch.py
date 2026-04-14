# import os

# from ament_index_python.packages import get_package_share_directory

# from launch import LaunchDescription
# from launch.actions import (DeclareLaunchArgument, GroupAction,
#                             IncludeLaunchDescription, SetEnvironmentVariable)
# from launch.conditions import IfCondition
# from launch.launch_description_sources import PythonLaunchDescriptionSource
# from launch.substitutions import LaunchConfiguration
# from launch_ros.actions import Node
# from launch_ros.actions import PushRosNamespace
# from nav2_common.launch import RewrittenYaml


# def generate_launch_description():
#     # Get the launch directory
#     bringup_dir = get_package_share_directory('robot_navigation2')
#     launch_dir = os.path.join(bringup_dir, 'launch')

#     # Create the launch configuration variables
#     namespace = LaunchConfiguration('namespace')
#     use_namespace = LaunchConfiguration('use_namespace')
#     map_yaml_file = LaunchConfiguration('map')
#     use_sim_time = LaunchConfiguration('use_sim_time')
#     params_file = LaunchConfiguration('params_file')
#     autostart = LaunchConfiguration('autostart')
#     use_composition = LaunchConfiguration('use_composition')
#     use_respawn = LaunchConfiguration('use_respawn')
#     log_level = LaunchConfiguration('log_level')
#     use_nav_rviz = LaunchConfiguration('nav_rviz')


#     # raise ValueError(map_yaml_file)

#     remappings = [('/tf', 'tf'),
#                   ('/tf_static', 'tf_static')]

#     # Create our own temporary YAML files that include substitutions
#     param_substitutions = {
#         'use_sim_time': use_sim_time,
#         'yaml_filename': map_yaml_file}

#     configured_params = RewrittenYaml(
#         source_file=params_file,
#         root_key=namespace,
#         param_rewrites=param_substitutions,
#         convert_types=True)

#     stdout_linebuf_envvar = SetEnvironmentVariable(
#         'RCUTILS_LOGGING_BUFFERED_STREAM', '1')

#     declare_namespace_cmd = DeclareLaunchArgument(
#         'namespace',
#         default_value='',
#         description='Top-level namespace')

#     declare_use_namespace_cmd = DeclareLaunchArgument(
#         'use_namespace',
#         default_value='false',
#         description='Whether to apply a namespace to the navigation stack')

#     declare_use_slam_cmd = DeclareLaunchArgument(
#         'use_slam',
#         default_value='True',
#         description='Whether run a SLAM')

#     declare_map_yaml_cmd = DeclareLaunchArgument(
#         'map',
#         default_value= os.path.join(bringup_dir,'map', 'RMUL.yaml'),
#         description='Full path to map yaml file to load')

#     declare_use_sim_time_cmd = DeclareLaunchArgument(
#         'use_sim_time',
#         default_value='True',
#         description='Use simulation (Gazebo) clock if true')

#     declare_params_file_cmd = DeclareLaunchArgument(
#         'params_file',
#         default_value=os.path.join(bringup_dir, 'params', 'nav2_params.yaml'),
#         description='Full path to the ROS2 parameters file to use for all launched nodes')


#     declare_autostart_cmd = DeclareLaunchArgument(
#         'autostart', default_value='True',
#         description='Automatically startup the nav2 stack')

#     declare_use_composition_cmd = DeclareLaunchArgument(
#         'use_composition', default_value='True',
#         description='Whether to use composed bringup')

#     declare_use_respawn_cmd = DeclareLaunchArgument(
#         'use_respawn', default_value='True',
#         description='Whether to respawn if a node crashes. Applied when composition is disabled.')

#     declare_log_level_cmd = DeclareLaunchArgument(
#         'log_level', default_value='info',
#         description='log level')
    
#     declare_nav_rviz_cmd = DeclareLaunchArgument(
#         'nav_rviz',
#         default_value='True',
#         description='Visualize navigation2 if true')

#     # Specify the actions
#     bringup_cmd_group = GroupAction([
#         PushRosNamespace(
#             condition=IfCondition(use_namespace),
#             namespace=namespace),

#         Node(
#             condition=IfCondition(use_composition),
#             name='nav2_container',
#             package='rclcpp_components',
#             executable='component_container_mt',
#             parameters=[configured_params, {'autostart': autostart}],
#             arguments=['--ros-args', '--log-level', log_level],
#             remappings=remappings,
#             output='screen'),

#         IncludeLaunchDescription(
#             PythonLaunchDescriptionSource(os.path.join(launch_dir, 'navigation_launch.py')),
#             launch_arguments={'namespace': namespace,
#                               'use_sim_time': use_sim_time,
#                               'autostart': autostart,
#                               'params_file': params_file,
#                               'use_composition': use_composition,
#                               'use_respawn': use_respawn,
#                               'container_name': 'nav2_container'}.items()),

#         IncludeLaunchDescription(
#             PythonLaunchDescriptionSource(os.path.join(launch_dir, 'rviz_launch.py')),
#             condition=IfCondition(use_nav_rviz)
#         ),
#     ])

#     # Create the launch description and populate
#     ld = LaunchDescription()

#     # Set environment variables

#     ld.add_action(stdout_linebuf_envvar)

#     # Declare the launch options
#     ld.add_action(declare_namespace_cmd)
#     ld.add_action(declare_use_namespace_cmd)
#     ld.add_action(declare_use_slam_cmd)
#     ld.add_action(declare_map_yaml_cmd)
#     ld.add_action(declare_use_sim_time_cmd)
#     ld.add_action(declare_params_file_cmd)
#     ld.add_action(declare_autostart_cmd)
#     ld.add_action(declare_use_composition_cmd)
#     ld.add_action(declare_use_respawn_cmd)
#     ld.add_action(declare_log_level_cmd)
#     ld.add_action(declare_nav_rviz_cmd)

#     # Add the actions to launch all of the navigation nodes
#     ld.add_action(bringup_cmd_group)


# #     from launch.actions import LogInfo
# #     log_action = LogInfo(
# #     msg=["地图路径为: ", map_yaml_file]
# # )
# #     ld.add_action(log_action)
    


#     return ld





# import os
# import launch
# import launch_ros
# from ament_index_python.packages import get_package_share_directory
# from launch.launch_description_sources import PythonLaunchDescriptionSource


# def generate_launch_description():
#     # 获取与拼接默认路径
#     fishbot_navigation2_dir = get_package_share_directory('robot_navigation2')
#     nav2_bringup_dir = get_package_share_directory('nav2_bringup')
#     rviz_config_dir = os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')

#     # 创建 Launch 配置
#     use_sim_time = launch.substitutions.LaunchConfiguration('use_sim_time', default='False')
#     nav2_param_path = launch.substitutions.LaunchConfiguration(
#         'params_file',
#         default=os.path.join(fishbot_navigation2_dir, 'config', 'nav2_params.yaml'))

#     return launch.LaunchDescription([
#         # 声明新的 Launch 参数
#         launch.actions.DeclareLaunchArgument(
#             'use_sim_time',
#             default_value=use_sim_time,
#             description='Use simulation (Gazebo) clock if true'
#         ),
#         launch.actions.DeclareLaunchArgument(
#             'params_file',
#             default_value=nav2_param_path,
#             description='Full path to param file to load'
#         ),

#         # 包含 bringup 启动文件，但禁用 map_server
#         launch.actions.IncludeLaunchDescription(
#             PythonLaunchDescriptionSource(
#                 [nav2_bringup_dir, '/launch', '/bringup_launch.py']),
#             # 使用 Launch 参数替换原有参数，并设置 use_map_topic := true
#             launch_arguments={
#                 'use_sim_time': use_sim_time,
#                 'params_file': nav2_param_path,
#                 'map': '',                  # 不提供地图文件路径
#                 'use_map_topic': 'true'     # ✅ 改为从 /map 话题获取地图
#             }.items(),
#         ),

#         # RVIZ 节点保持不变
#         launch_ros.actions.Node(
#             package='rviz2',
#             executable='rviz2',
#             name='rviz2',
#             arguments=['-d', rviz_config_dir],
#             parameters=[{'use_sim_time': use_sim_time}],
#             output='screen'),
#     ])


import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # 获取与拼接默认路径
    bringup_dir = get_package_share_directory(
        'bringup')
    robot_navigation_dir = get_package_share_directory(
        'robot_navigation2')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    rviz_config_dir = os.path.join(
        nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')
    
    # 创建 Launch 配置
    use_sim_time = launch.substitutions.LaunchConfiguration(
        'use_sim_time', default='False')
    map_yaml_path = launch.substitutions.LaunchConfiguration(
        'map', default=os.path.join(bringup_dir, 'map', 'test.yaml'))
    nav2_param_path = launch.substitutions.LaunchConfiguration(
        'params_file', default=os.path.join(bringup_dir, 'config', 'nav','nav2_params_real.yaml'))

    return launch.LaunchDescription([
        # 声明新的 Launch 参数
        launch.actions.DeclareLaunchArgument('use_sim_time', default_value=use_sim_time,
                                             description='Use simulation (Gazebo) clock if true'),
        launch.actions.DeclareLaunchArgument('map', default_value=map_yaml_path,
                                             description='Full path to map file to load'),
        launch.actions.DeclareLaunchArgument('params_file', default_value=nav2_param_path,
                                             description='Full path to param file to load'),

        launch.actions.IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [nav2_bringup_dir, '/launch', '/bringup_launch.py']),
            # 使用 Launch 参数替换原有参数
            launch_arguments={
                'map': map_yaml_path,
                'use_sim_time': use_sim_time,
                'params_file': nav2_param_path}.items(),
        ),
        launch_ros.actions.Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'),
    ])