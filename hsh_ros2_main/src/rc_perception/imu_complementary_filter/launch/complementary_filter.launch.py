from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():


    imu_complementary_filter_params = os.path.join(
        get_package_share_directory('imu_complementary_filter'),
         'config',
         'complementary_filter.yaml'
    )


    with open(imu_complementary_filter_params, 'r') as f:
        params = yaml.safe_load(f)
        imu_data_raw = params['complementary_filter']['ros__parameters']['imu_data_raw']



    return LaunchDescription(
        [
            Node(
                package='imu_complementary_filter',
                executable='complementary_filter_node',
                name='complementary_filter_gain_node',
                output='screen',
                parameters=[imu_complementary_filter_params],
                remappings=[
                	('/imu/data_raw', imu_data_raw),
                ]
            )
        ]
    )
