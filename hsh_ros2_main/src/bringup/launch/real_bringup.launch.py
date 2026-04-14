import os
import yaml,launch,launch_ros

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, GroupAction, TimerAction,SetEnvironmentVariable
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch.conditions import LaunchConfigurationEquals, LaunchConfigurationNotEquals, IfCondition
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, TextSubstitution
from launch.substitutions import PythonExpression
from nav2_common.launch import RewrittenYaml  # 👈 新增：用于参数替换
from launch.actions import LogInfo

def generate_launch_description():
    # 获取launch文件目录
    bringup_dir = get_package_share_directory('bringup')
    navigation2_launch_dir = os.path.join(get_package_share_directory('robot_navigation2'), 'launch')
    

    # 创建外部终端参数
    world = LaunchConfiguration('world')
    localization = LaunchConfiguration('localization')
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_lio_rviz = LaunchConfiguration('lio_rviz')
    use_nav_rviz = LaunchConfiguration('nav_rviz')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='False',
        description='Use reality (Gazebo) clock if true')

    declare_use_lio_rviz_cmd = DeclareLaunchArgument(
        'lio_rviz',
        default_value='False',
        description='Visualize FAST_LIO or Point_LIO cloud_map if true')
    
    declare_nav_rviz_cmd = DeclareLaunchArgument(
        'nav_rviz',
        default_value='True',
        description='Visualize navigation2 if true')

    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value='328',
        description='Select world (map file, pcd file, world file share the same name prefix as the this parameter)')

    declare_mode_cmd = DeclareLaunchArgument(
        'mode',
        default_value='',
        description='Choose mode: nav, mapping')
    
    declare_LIO_cmd = DeclareLaunchArgument(
        'lio',
        default_value='fast_lio',
        description='Choose lio alogrithm: fastlio or pointlio')

    declare_localization_cmd = DeclareLaunchArgument(
        'localization',
        default_value='',
        description='Choose localization method: slam_toolbox, amcl, icp')
    #####################################################################################################################



    
    #robot_description
    launch_params = yaml.safe_load(open(os.path.join(
    get_package_share_directory('bringup'), 'config','drivers', 'measurement_params_real.yaml')))

    robot_description = Command(['xacro ', os.path.join(
    get_package_share_directory('bringup'), 'urdf', 'sentry_robot_real.xacro'),
    ' xyz:=', launch_params['base_link2livox_frame']['xyz'], ' rpy:=', launch_params['base_link2livox_frame']['rpy']])
    #####################################################################################################################


    #pointcloud_to_laserscan
    pointcloud_to_laserscan_params = os.path.join(
        bringup_dir,
        'config',
        'pointcloud',
        'pointcloud_to_laserscan_params.yaml'
    )   
    with open(pointcloud_to_laserscan_params, 'r') as f:
        params = yaml.safe_load(f)
        cloud_in_topic = params['pointcloud_to_laserscan']['ros__parameters']['cloud_in_topic']
        scan_out_topic = params['pointcloud_to_laserscan']['ros__parameters']['scan_out_topic']
    #####################################################################################################################
    
    
    
    #serial_params
    serial_params = os.path.join(
        bringup_dir,
        'config',
        'drivers',
        'serial_configs.yaml'
    )
    #####################################################################################################################

    
    #linefit_ground_segementation
    segmentation_params = os.path.join(
        bringup_dir, 
        'config',
        'pointcloud',
        'segmentation_real.yaml'
    )
    #####################################################################################################################

    
    #FAST_LIO2
    fastlio_mid360_params = os.path.join(
        bringup_dir,
         'config',
         'lio',
         'fastlio_mid360_real.yaml'
    )
    fastlio_rviz_cfg_dir = os.path.join(bringup_dir, 'rviz', 'fastlio.rviz')
    #####################################################################################################################

    
    #POINT_LIO2
    pointlio_mid360_params = os.path.join(
        bringup_dir,
         'config',
         'lio',
         'pointlio_mid360_real.yaml'
    )
    pointlio_rviz_cfg_dir = os.path.join(bringup_dir, 'rviz', 'pointlio.rviz')
    #####################################################################################################################



    #imu_complementary_filter
    imu_complementary_filter_params = os.path.join(
        bringup_dir,
         'config',
         'drivers',
         'complementary_filter.yaml'
    )


    with open(imu_complementary_filter_params, 'r') as f:
        params = yaml.safe_load(f)
        imu_data_raw = params['complementary_filter']['ros__parameters']['imu_data_raw']
        
    
    #####################################################################################################################

    #slam_toolbox
    slam_toolbox_map_dir = PathJoinSubstitution([
        bringup_dir,
        'map',
        PythonExpression(["'", world, "'"])
    ])


    slam_toolbox_localization_file_dir = os.path.join(
        bringup_dir,
         'config',
         'mapper',
         'mapper_params_localization_real.yaml'
    )


    slam_toolbox_mapping_file_dir = os.path.join(
        bringup_dir,
         'config',
         'mapper',
         'mapper_params_online_async_real.yaml'
    )
    #####################################################################################################################

    
    #navigation2
    nav2_map_dir = PathJoinSubstitution([
        bringup_dir,
        'map',
        PythonExpression(["'", world, ".yaml'"])
    ])
    
    
    nav2_params_file_dir = os.path.join(
        bringup_dir, 
        'config', 
        'nav',
        'nav2_params_real.yaml'
    )


    #####################################################################################################################

    
    #icp_registration
    icp_pcd_dir = PathJoinSubstitution([
        bringup_dir,
        'PCD',
        PythonExpression(["'", world, ".pcd'"])
    ])


    icp_registration_params_dir = os.path.join(
        bringup_dir,
         'config',
         'location',
         'icp_registration_real.yaml'
        )
    #####################################################################################################################


    
    #Livox_ros_driver2
    xfer_format   = 0    # 0-Pointcloud2(PointXYZRTL), 1-customized pointcloud format
    multi_topic   = 0    # 0-All LiDARs share the same topic, 1-One LiDAR one topic
    data_src      = 0    # 0-lidar, others-Invalid data src
    publish_freq  = 10.0 # freqency of publish, 5.0, 10.0, 20.0, 50.0, etc.
    output_type   = 0
    frame_id      = 'livox_frame'
    lvx_file_path = '/home/livox/livox_test.lvx'
    cmdline_bd_code = 'livox0000000001'

    # cur_path = os.path.split(os.path.realpath(__file__))[0] + '/'
    # cur_config_path = cur_path + '../config'
    # user_config_path = os.path.join(cur_config_path, 'MID360_config.json')
    user_config_path = os.path.join(
        bringup_dir,
         'config',
         'drivers',
         'MID360_config.json'
        )

    livox_ros2_params = [
        {"xfer_format": xfer_format},
        {"multi_topic": multi_topic},
        {"data_src": data_src},
        {"publish_freq": publish_freq},
        {"output_data_type": output_type},
        {"frame_id": frame_id},
        {"lvx_file_path": lvx_file_path},
        {"user_config_path": user_config_path},
        {"cmdline_input_bd_code": cmdline_bd_code}
    ]
    #####################################################################################################################


    start_robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description
        }],
        output='screen'
    )

    # Specify the actions
    start_livox_ros_driver2_node = Node(
        package='livox_ros_driver2',
        executable='livox_ros_driver2_node',
        name='livox_lidar_publisher',
        output='screen',
        parameters=livox_ros2_params
    )

    bringup_imu_complementary_filter_node = Node(
        package='imu_complementary_filter',
        executable='complementary_filter_node',
        name='complementary_filter_gain_node',
        output='screen',
        parameters=[imu_complementary_filter_params],
        remappings=[
            ('/imu/data_raw', imu_data_raw),
        ]
    )

    bringup_linefit_ground_segmentation_node = Node(
        package='linefit_ground_segmentation_ros',
        executable='ground_segmentation_node',
        output='screen',
        parameters=[segmentation_params]
    )
    
    bringup_pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan', executable='pointcloud_to_laserscan_node',
        remappings=[('cloud_in',  [cloud_in_topic]),
                    ('scan',  [scan_out_topic])],
        parameters=[pointcloud_to_laserscan_params],
        name='pointcloud_to_laserscan'
    )
    

    bringup_LIO_group = GroupAction([
        Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            # Copy from the 'livox_joint' in 'sentry_robot.xacro'.
            arguments=[
                # Useless arguments, provided by LIO in publish_odometry() function
                # '--x', '0.0',
                # '--y', '0.0',
                # '--z', '0.0',
                # '--roll', '0.0',
                # '--pitch', '0.0',
                # '--yaw', '0.0',
                '--frame-id', 'odom',
                '--child-frame-id', 'lidar_odom'
            ],
        ),

        GroupAction(
            condition = LaunchConfigurationEquals('lio', 'fastlio'),
            actions=[
            Node(
                package='fast_lio',
                executable='fastlio_mapping',
                parameters=[
                    fastlio_mid360_params,
                    {use_sim_time: use_sim_time}
                ],
                output='screen'
            ),
            Node(
                package='rviz2',
                executable='rviz2',
                arguments=['-d', fastlio_rviz_cfg_dir],
                condition = IfCondition(use_lio_rviz),
            ),
        ]),

        GroupAction(
            condition = LaunchConfigurationEquals('lio', 'pointlio'),
            actions=[
            Node(
                package='point_lio',
                executable='pointlio_mapping',
                name='laserMapping',
                output='screen',
                parameters=[
                    pointlio_mid360_params,
                    {'use_sim_time': use_sim_time,
                    'use_imu_as_input': False,  # Change to True to use IMU as input of Point-LIO
                    'prop_at_freq_of_imu': True,
                    'check_satu': True,
                    'init_map_size': 10,
                    'point_filter_num': 3,  # Options: 1, 3
                    'space_down_sample': True,
                    'filter_size_surf': 0.5,  # Options: 0.5, 0.3, 0.2, 0.15, 0.1
                    'filter_size_map': 0.5,  # Options: 0.5, 0.3, 0.15, 0.1
                    'ivox_nearby_type': 6,   # Options: 0, 6, 18, 26
                    'runtime_pos_log_enable': False}
                ],
            ),
            Node(
                package='rviz2',
                executable='rviz2',
                arguments=['-d', pointlio_rviz_cfg_dir],
                condition = IfCondition(use_lio_rviz),
            )
        ])
    ])

    start_localization_group = GroupAction(
        condition = LaunchConfigurationEquals('mode', 'nav'),
        actions=[
            Node(
                condition = LaunchConfigurationEquals('localization', 'slam_toolbox'),
                package='slam_toolbox',
                executable='localization_slam_toolbox_node',
                name='slam_toolbox',
                parameters=[
                    slam_toolbox_localization_file_dir,
                    {'use_sim_time': use_sim_time,
                    'map_file_name': slam_toolbox_map_dir,
                    'map_start_pose': [0.0, 0.0, 0.0]}
                ],
            ),

            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(navigation2_launch_dir,'localization_amcl_launch.py')),
                condition = LaunchConfigurationEquals('localization', 'amcl'),
                launch_arguments = {
                    'use_sim_time': use_sim_time,
                    'params_file': nav2_params_file_dir,
                    'map': nav2_map_dir}.items()
            ),

            TimerAction(
                period=7.0,
                actions=[
                    Node(
                        condition=LaunchConfigurationEquals('localization', 'icp'),
                        package='icp_registration',
                        executable='icp_registration_node',
                        output='screen',
                        parameters=[
                            icp_registration_params_dir,
                            {'use_sim_time': use_sim_time,
                                'pcd_path': icp_pcd_dir}
                        ],
                        # arguments=['--ros-args', '--log-level', ['icp_registration:=', 'DEBUG']]
                    )
                ]
            ),

            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(navigation2_launch_dir, 'map_server_launch.py')),
                condition = LaunchConfigurationNotEquals('localization', 'slam_toolbox'),
                launch_arguments={
                    'use_sim_time': use_sim_time,
                    'map': nav2_map_dir,
                    'params_file': nav2_params_file_dir,
                    'container_name': 'nav2_container'}.items())
        ]
    )

    bringup_fake_vel_transform_node = Node(
        package='fake_vel_transform',
        executable='fake_vel_transform_node',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'spin_speed': 0.0 # rad/s
        }]
    )

    start_mapping = Node(
        condition = LaunchConfigurationEquals('mode', 'mapping'),
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[
            slam_toolbox_mapping_file_dir,
            {'use_sim_time': use_sim_time,}
        ],
    )
    

    start_navigation2_group = GroupAction([
        #================== 1. 启动 Nav2 容器（如果使用组合模式）==================
        Node(
            package='rclcpp_components',
            executable='component_container_mt',
            name='nav2_container',
            parameters=[
                RewrittenYaml(
                    source_file=nav2_params_file_dir,
                    param_rewrites={
                        'use_sim_time': use_sim_time,
                        'yaml_filename': nav2_map_dir 
                    },
                    convert_types=True
                )
            ],
            output='screen',
            # condition=IfCondition(PythonExpression(["'", LaunchConfiguration('mode'), "' == 'nav'"]))
        ),
        # ================== 4. 启动导航栈（navigation_launch.py）==================
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(navigation2_launch_dir, 'navigation_launch.py')),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'params_file': RewrittenYaml(
                    source_file=nav2_params_file_dir,
                    param_rewrites={
                        'use_sim_time': use_sim_time,
                        'yaml_filename': nav2_map_dir 
                    },
                    convert_types=True
                ),
            }.items(),
            # condition=IfCondition(PythonExpression(["'", LaunchConfiguration('mode'), "' == 'nav'"]))
        ),

        # ================== 5. 启动 RViz（如果启用）==================
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(navigation2_launch_dir, 'rviz_launch.py')),
            launch_arguments={
                'use_sim_time': use_sim_time,
            }.items(),
            condition=IfCondition(use_nav_rviz)
        ),

    ])


    
    # start_navigation2 = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(os.path.join(navigation2_launch_dir, 'bringup_navigation2.launch.py')),
    #     launch_arguments={
    #         'use_sim_time': use_sim_time,
    #         'map': nav2_map_dir,
    #         'params_file': nav2_params_file_dir,
    #         'nav_rviz': use_nav_rviz}.items()
    # )
    


    # start_navigation2_bringup = launch.actions.IncludeLaunchDescription(
    #     launch.launch_description_sources.PythonLaunchDescriptionSource(
    #         os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'bringup_launch.py')
    #     ),
    #     launch_arguments={
    #         'use_sim_time': use_sim_time,
    #         'map': nav2_map_dir,
    #         'params_file': nav2_params_file_dir
    #     }.items()
    # )


    # start_navigation2_rviz =IncludeLaunchDescription(
    #         PythonLaunchDescriptionSource(os.path.join(navigation2_launch_dir, 'rviz_launch.py')),
    #         launch_arguments={
    #             'use_sim_time': use_sim_time,
    #         }.items(),
    #         condition=IfCondition(use_nav_rviz)
    #     )


    # start_navigation2_group = launch.actions.GroupAction([
    #     start_navigation2_bringup,
    #     start_navigation2_rviz
    # ])



    bringup_serial_node = Node(
            package='serial_node',
            executable='serial_twist_publisher',
            name='serial_twist_publisher',
            parameters=[serial_params],
            output='screen'
        )

    waypoint_dir = os.path.join(get_package_share_directory('multi_waypoint_navigator'), 'launch')
    bringup_waypoint = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(waypoint_dir, 'navigator.launch.py')),
        
    )



    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_use_lio_rviz_cmd)
    ld.add_action(declare_nav_rviz_cmd)
    ld.add_action(declare_world_cmd)
    ld.add_action(declare_mode_cmd)
    ld.add_action(declare_localization_cmd)
    ld.add_action(declare_LIO_cmd)





    
    ld.add_action(start_robot_state_publisher_cmd)
    ld.add_action(start_livox_ros_driver2_node)
    ld.add_action(bringup_LIO_group)
    # ld.add_action(bringup_imu_complementary_filter_node)
    # ld.add_action(bringup_linefit_ground_segmentation_node)
    ld.add_action(bringup_pointcloud_to_laserscan_node)
    
    ld.add_action(start_localization_group)
    # ld.add_action(bringup_fake_vel_transform_node)
    ld.add_action(start_mapping)
    # ld.add_action(start_navigation2)
    # ld.add_action(bringup_serial_node)



    #  # 👉 添加集成的 Nav2 组（替换原来的 IncludeLaunchDescription）
    ld.add_action(start_navigation2_group)
    # ld.add_action(bringup_waypoint)
    
    # 打印路径到终端
#     from launch.actions import LogInfo
#     log_action = LogInfo(
#     msg=["地图路径为: ", nav2_map_dir]
# )
#     ld.add_action(log_action)
    return ld

