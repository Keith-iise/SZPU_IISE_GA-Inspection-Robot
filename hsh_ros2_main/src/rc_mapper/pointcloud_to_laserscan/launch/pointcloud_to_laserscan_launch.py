from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os
import yaml


def generate_launch_description():

    config_dir = os.path.join(
        get_package_share_directory('pointcloud_to_laserscan'),
        'config',
        'pointcloud_to_laserscan_params.yaml'
    )   
     # 加载并解析 YAML 文件
    with open(config_dir, 'r') as f:
        params = yaml.safe_load(f)
        cloud_in_topic = params['pointcloud_to_laserscan']['ros__parameters']['cloud_in_topic']
        scan_out_topic = params['pointcloud_to_laserscan']['ros__parameters']['scan_out_topic']
    



    bringup_pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan', executable='pointcloud_to_laserscan_node',
        remappings=[('cloud_in',  [cloud_in_topic]),
                    ('scan',  [scan_out_topic])],
        parameters=[config_dir],
        name='pointcloud_to_laserscan'
    )
    return LaunchDescription([
        bringup_pointcloud_to_laserscan_node,

    ])




# from launch import LaunchDescription
# from launch.actions import DeclareLaunchArgument
# from launch.substitutions import LaunchConfiguration
# from launch_ros.actions import Node

# from ament_index_python.packages import get_package_share_directory
# import os

# def generate_launch_description():

#     config_dir = os.path.join(
#         get_package_share_directory('pointcloud_to_laserscan'),
#         'config',
#         'pointcloud_to_laserscan_params.yaml'
#     )


#     # 声明可传入的参数
#     scanner_arg = DeclareLaunchArgument(
#         name='scanner', default_value='scanner',
#         description='Namespace for sample topics'
#     )

#     target_frame_arg = DeclareLaunchArgument(
#         name='target_frame', default_value='livox_frame',
#         description='Target frame to transform pointcloud into'
#     )

#     min_height_arg = DeclareLaunchArgument(
#         name='min_height', default_value='-1000.0',
#         description='Minimum height of point cloud to consider'
#     )

#     max_height_arg = DeclareLaunchArgument(
#         name='max_height', default_value='1000.0',
#         description='Maximum height of point cloud to consider'
#     )

#     cloud_in_topic_arg = DeclareLaunchArgument(
#         name='cloud_in_topic', default_value='/segmentation/obstacle',
#         description='Input PointCloud2 topic to subscribe to'
#     )

#     scan_out_topic_arg = DeclareLaunchArgument(
#         name='scan_out_topic', default_value='/scan',
#         description='Output LaserScan topic to publish'
#     )

#     # # 构建参数字典
#     # scan_params = [{
#     #     'target_frame': LaunchConfiguration('target_frame'),
#     #     'transform_tolerance': 0.01,
#     #     'min_height': LaunchConfiguration('min_height'),
#     #     'max_height': LaunchConfiguration('max_height'),
#     #     'angle_min': -3.14159,
#     #     'angle_max': 3.14159,
#     #     'angle_increment': 0.0043,
#     #     'scan_time': 0.3333,
#     #     'range_min': 0.45,
#     #     'range_max': 10.0,
#     #     'use_inf': True,
#     #     'inf_epsilon': 1.0
#     # }]

#     return LaunchDescription([
#         scanner_arg,
#         target_frame_arg,
#         min_height_arg,
#         max_height_arg,
#         cloud_in_topic_arg,
#         scan_out_topic_arg,

#         # # 静态 TF
#         # Node(
#         #     package='tf2_ros',
#         #     executable='static_transform_publisher',
#         #     name='static_transform_publisher',
#         #     arguments=[
#         #         '--x', '0', '--y', '0', '--z', '0',
#         #         '--qx', '0', '--qy', '0', '--qz', '0', '--qw', '1',
#         #         '--frame-id', 'base_link', '--child-frame-id', 'livox_frame'
#         #     ]
#         # ),
#         # 点云转激光雷达扫描
#         Node(
#             package='pointcloud_to_laserscan',
#             executable='pointcloud_to_laserscan_node',
#             remappings=[
#                 ('cloud_in', LaunchConfiguration('cloud_in_topic')),   # 可配置输入点云话题
#                 ('scan', LaunchConfiguration('scan_out_topic'))       # 可配置输出 scan 话题
#             ],
#             parameters=[
#                 config_dir,  # ← 添加了逗号
#                 {
#                     "target_frame": LaunchConfiguration("target_frame"),
#                     "min_height": LaunchConfiguration("min_height"),
#                     "max_height": LaunchConfiguration("max_height"),
#                 }
#             ],
#             name='pointcloud_to_laserscan',
#             arguments=['--ros-args', '--log-level', 'info'])
#     ])
#     #     # 点云转激光雷达扫描
#     #     Node(
#     #         package='pointcloud_to_laserscan',
#     #         executable='pointcloud_to_laserscan_node',
#     #         remappings=[
#     #             ('cloud_in', LaunchConfiguration('cloud_in_topic')),   # 可配置输入点云话题
#     #             ('scan', LaunchConfiguration('scan_out_topic'))       # 可配置输出 scan 话题
#     #         ],
#     #         parameters=[
#     #         config_dir,
#     #             {
#     #                 "target_frame": LaunchConfiguration("target_frame"),
#     #                 "min_height": LaunchConfiguration("min_height"),
#     #                 "max_height": LaunchConfiguration("max_height"),
#     #             }
            
#     #         ]
#     #         name='pointcloud_to_laserscan',
#     #         arguments=['--ros-args', '--log-level', 'info']
#     #     )
#     # ])


# from launch import LaunchDescription
# from launch.actions import DeclareLaunchArgument
# from launch.substitutions import LaunchConfiguration
# from launch_ros.actions import Node


# def generate_launch_description():
#     return LaunchDescription([
#         DeclareLaunchArgument(
#             name='scanner', default_value='scanner',
#             description='Namespace for sample topics'
#         ),
#         Node(
#             package='tf2_ros',
#             executable='static_transform_publisher',
#             name='static_transform_publisher',
#             arguments=[
#                 '--x', '0', '--y', '0', '--z', '0',
#                 '--qx', '0', '--qy', '0', '--qz', '0', '--qw', '1',
#                 '--frame-id', 'base_link', '--child-frame-id' , 'livox_frame'
#             ]
#         ),
#         Node(
#             package='pointcloud_to_laserscan', executable='pointcloud_to_laserscan_node',
#             remappings=[
#                 ('cloud_in', '/livox/lidar'),   # 直接订阅真实点云
#                 ('scan', '/scan')  # 输出 /scanner/scan
#             ],
#             parameters=[{
#                 'target_frame': 'livox_frame',  # 坐标系要与 TF 匹配
#                 'transform_tolerance': 0.01,
#                 'min_height': -0.09,  # 可根据实际调整
#                 'max_height': 0.35,
#                 'angle_min': -3.14159,
#                 'angle_max': 3.14159,
#                 'angle_increment': 0.0043,
#                 'scan_time': 0.3333,
#                 'range_min': 0.45,
#                 'range_max': 10.0,
#                 'use_inf': True,
#                 'inf_epsilon': 1.0
#             }],
#             name='pointcloud_to_laserscan',
#             arguments=['--ros-args', '--log-level', 'info']
#         )
#     ])