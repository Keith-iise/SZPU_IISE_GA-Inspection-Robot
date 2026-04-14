import launch,os
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


package_name = 'expression_show'
show_node = 'show_node'

def generate_launch_description():

    expression_show_path = get_package_share_directory(package_name)
    param_file = os.path.join(expression_show_path, 'config', 'show.yaml')


    action_show = Node(
        package=package_name,
        executable=show_node,
        name=show_node,
        parameters=[param_file],
        output='screen'
    )

    return launch.LaunchDescription([
        action_show,

    ])






