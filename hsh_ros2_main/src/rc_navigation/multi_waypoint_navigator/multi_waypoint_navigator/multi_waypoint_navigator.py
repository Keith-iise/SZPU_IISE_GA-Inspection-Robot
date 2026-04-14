#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from std_msgs.msg import Int16
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
import yaml
import os
from ament_index_python.packages import get_package_share_directory
from math import atan2, sin, cos, sqrt
from action_msgs.msg import GoalStatus  # 正确导入

class MultiWaypointNavigator(Node):
    def __init__(self):
        super().__init__('multi_waypoint_navigator')
        
        # 声明参数
        self.declare_parameter('waypoints_file', 'waypoints.yaml')
        self.declare_parameter('position_tolerance', 0.25)
        self.declare_parameter('orientation_tolerance', 0.5)
        self.declare_parameter('wait_time_at_waypoint', 5.0)
        
        # 获取参数
        waypoints_file = self.get_parameter('waypoints_file').value
        self.position_tolerance = self.get_parameter('position_tolerance').value
        self.orientation_tolerance = self.get_parameter('orientation_tolerance').value
        self.wait_time_at_waypoint = self.get_parameter('wait_time_at_waypoint').value
        
        # 加载航点
        self.waypoints = self.load_waypoints(waypoints_file)
        self.current_waypoint_index = 0
        self.is_returning_to_origin = False
        self.is_navigating = False
        self.is_waiting = False
        
        # TF2监听
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # 导航动作客户端
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.pub_light = self.create_publisher(Int16, 'light', 10)
        self.pub_plane = self.create_publisher(Int16, 'plane', 10)

        light_msg = Int16()
        light_msg.data = 0x01
        self.pub_light.publish(light_msg)
        
        # 订阅里程计
        self.current_pose = None
        self.odom_subscription = self.create_subscription(
            Odometry, 'odom', self.odom_callback, 10)
        
        # 等待动作服务器（延长超时时间至20秒，确保导航栈初始化完成）
        self.get_logger().info("等待 navigate_to_pose 动作服务器...")
        if not self.nav_to_pose_client.wait_for_server(timeout_sec=20.0):
            self.get_logger().error("动作服务器未启动，退出")
            return
        
        self.get_logger().info("动作服务器已连接！")
        
        # 启动定时器
        self.start_timer = self.create_timer(2.0, self.start_navigation)
        
        # 状态变量
        self.goal_handle = None
        self.result_future = None

    def start_navigation(self):
        self.destroy_timer(self.start_timer)
        self.get_logger().info(f"=== 启动导航，初始航点索引：{self.current_waypoint_index} ===")
        self.navigate_to_next_waypoint()

    def load_waypoints(self, waypoints_file):
        if not waypoints_file.startswith('/'):
            package_share_dir = get_package_share_directory('multi_waypoint_navigator')
            waypoints_file = os.path.join(package_share_dir, 'config', waypoints_file)
        
        self.get_logger().info(f"从 {waypoints_file} 加载航点")
        try:
            with open(waypoints_file, 'r') as file:
                config = yaml.safe_load(file)
                waypoints = config.get('waypoints', [])
                self.get_logger().info(f"成功加载 {len(waypoints)} 个航点：{[wp.get('name', f'点{i}') for i, wp in enumerate(waypoints)]}")
                return waypoints
        except Exception as e:
            self.get_logger().error(f"加载航点失败：{e}")
            return []

    def odom_callback(self, msg):
        self.current_pose = msg.pose.pose

    def create_pose_stamped(self, x, y, yaw):
        """确保目标点消息格式正确（重点：时间戳和坐标系）"""
        pose_stamped = PoseStamped()
        pose_stamped.header.frame_id = 'map'  # 必须与导航栈使用的全局坐标系一致
        pose_stamped.header.stamp = self.get_clock().now().to_msg()  # 确保时间戳有效
        pose_stamped.pose.position.x = x
        pose_stamped.pose.position.y = y
        pose_stamped.pose.position.z = 0.0
        pose_stamped.pose.orientation.x = 0.0
        pose_stamped.pose.orientation.y = 0.0
        pose_stamped.pose.orientation.z = sin(yaw / 2)
        pose_stamped.pose.orientation.w = cos(yaw / 2)
        return pose_stamped

    def navigate_to_pose(self, pose_stamped):
        if self.is_navigating or self.is_waiting:
            self.get_logger().warn(f"当前状态：导航中={self.is_navigating}，等待中={self.is_waiting}，跳过新目标")
            return
        
        self.is_navigating = True

        light_msg = Int16()
        light_msg.data = 0x02
        self.pub_light.publish(light_msg)

        plane_msg = Int16()
        plane_msg.data = 0x01
        self.pub_plane.publish(plane_msg)


        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose_stamped
        
        yaw = atan2(2*(pose_stamped.pose.orientation.z*pose_stamped.pose.orientation.w), 
                    1-2*(pose_stamped.pose.orientation.z**2))
        self.get_logger().info(
            f"=== 发送导航目标：索引={self.current_waypoint_index}，x={pose_stamped.pose.position.x:.2f}, "
            f"y={pose_stamped.pose.position.y:.2f}, yaw={yaw:.2f}，坐标系={pose_stamped.header.frame_id} ==="
        )
        
        self.send_goal_future = self.nav_to_pose_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        self.send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.get_logger().error(f"目标（索引={self.current_waypoint_index}）被服务器拒绝，3秒后重试（延长重试间隔，避免频繁发送）")
            self.is_navigating = False
            self.retry_timer = self.create_timer(3.0, self._retry_navigation)  # 延长重试间隔至3秒
            return
        self.get_logger().info(f"目标（索引={self.current_waypoint_index}）已被服务器接受，等待完成...")
        self.result_future = self.goal_handle.get_result_async()
        self.result_future.add_done_callback(self.get_result_callback)

    def _retry_navigation(self):
        self.destroy_timer(self.retry_timer)
        self.get_logger().info(f"重试导航：索引={self.current_waypoint_index}")
        self.navigate_to_next_waypoint()

    def feedback_callback(self, feedback_msg):
        if not self.current_pose:
            return
        goal_x = feedback_msg.feedback.current_goal.pose.position.x
        goal_y = feedback_msg.feedback.current_goal.pose.position.y
        curr_x = self.current_pose.position.x
        curr_y = self.current_pose.position.y
        distance = sqrt((goal_x - curr_x)**2 + (goal_y - curr_y)** 2)
        self.get_logger().debug(
            f"距离目标（索引={self.current_waypoint_index}）：{distance:.2f}米，"
            f"容忍度：{self.position_tolerance}米"
        )

    def get_result_callback(self, future):
        """修复：删除STATUS_LOST，仅保留官方定义的状态码"""
        result = future.result()
        self.is_navigating = False

        if result.status == GoalStatus.STATUS_SUCCEEDED:
        # >>> 修改：仅当不是返回原点时，才设置 plane = 0x02
            if not self.is_returning_to_origin:
                plane_msg = Int16()  # 注意：这里应该是 Int16！
                plane_msg.data = 0x02
                self.pub_plane.publish(plane_msg)
            # 如果是返回原点，则不发布 plane=0x02，保持之前的状态（通常是 0x01）

            self.wait_at_waypoint()
        else:
            light_msg = Int16()
            light_msg.data = 0x01
            self.pub_light.publish(light_msg)
            self.get_logger().warn(f"导航未成功，3秒后重试当前航点（索引={self.current_waypoint_index}）")
            self.retry_timer = self.create_timer(3.0, self._retry_navigation)
        
        # 正确的状态码映射（仅保留官方定义的状态）
        status_map = {
            GoalStatus.STATUS_SUCCEEDED: "成功",
            GoalStatus.STATUS_ABORTED: "中止（导航失败）",
            GoalStatus.STATUS_CANCELED: "已取消",
            GoalStatus.STATUS_ACCEPTED: "已接受（处理中）",
            GoalStatus.STATUS_EXECUTING: "执行中",
            GoalStatus.STATUS_CANCELING: "取消中"
        }
        status_str = status_map.get(result.status, f"未知状态码：{result.status}")
        
        self.get_logger().info(
            f"导航结果（索引={self.current_waypoint_index}）：{status_str}，"
            f"状态码：{result.status}"
        )
        
        if result.status == GoalStatus.STATUS_SUCCEEDED:
            self.wait_at_waypoint()
        else:
            self.get_logger().warn(f"导航未成功，3秒后重试当前航点（索引={self.current_waypoint_index}）")
            self.retry_timer = self.create_timer(3.0, self._retry_navigation)

    def wait_at_waypoint(self):
        if self.is_waiting:
            self.get_logger().warn("已在等待中，跳过重复等待")
            return
        self.is_waiting = True
        
         # >>> 统一：只要到达航点并等待，就设置 light = 0x03
        light_msg = Int16()
        light_msg.data = 0x03
        self.pub_light.publish(light_msg)

        if self.is_returning_to_origin:
            wait_time = 10.0
            self.get_logger().info(f"回到原点，等待 {wait_time} 秒后重启循环")
        else:
            wait_time = self.wait_time_at_waypoint
            waypoint_name = self.waypoints[self.current_waypoint_index].get(
                'name', f'航点{self.current_waypoint_index+1}')
            self.get_logger().info(f"到达 {waypoint_name}，等待 {wait_time} 秒")
        
        self.wait_timer = self.create_timer(wait_time, self.on_wait_finish)

    def on_wait_finish(self):
        self.destroy_timer(self.wait_timer)
        self.is_waiting = False
        self.get_logger().info(f"等待结束（索引={self.current_waypoint_index}），准备切换下一个目标")
        
        if self.is_returning_to_origin:
            self.is_returning_to_origin = False
            self.current_waypoint_index = 0
            self.get_logger().info("="*50)
            self.get_logger().info(f"循环完成，重置索引为 {self.current_waypoint_index}，准备重启")
            self.get_logger().info("="*50)
            self.restart_timer = self.create_timer(0.5, self._restart_navigation)
            return
        
        old_index = self.current_waypoint_index
        self.current_waypoint_index += 1
        self.get_logger().info(
            f"索引更新：{old_index} → {self.current_waypoint_index}，"
            f"总航点数：{len(self.waypoints)}"
        )
        
        if self.current_waypoint_index >= len(self.waypoints):
            self.get_logger().info(f"索引 {self.current_waypoint_index} 超过总航点数，准备返回原点")
            self.is_returning_to_origin = True
            self.navigate_to_origin()
        else:
            self.get_logger().info(f"导航到下一个航点（索引={self.current_waypoint_index}）")
            self.navigate_to_next_waypoint()

    def _restart_navigation(self):
        self.destroy_timer(self.restart_timer)
        self.get_logger().info(f"重启导航，当前索引：{self.current_waypoint_index}")
        self.navigate_to_next_waypoint()

    def navigate_to_next_waypoint(self):
        if not self.waypoints:
            self.get_logger().error("航点列表为空，无法导航")
            return
        
        if self.current_waypoint_index < 0 or self.current_waypoint_index >= len(self.waypoints):
            self.get_logger().warn(
                f"索引 {self.current_waypoint_index} 无效（总航点数：{len(self.waypoints)}），"
                f"重置为0"
            )
            self.current_waypoint_index = 0
        
        waypoint = self.waypoints[self.current_waypoint_index]
        pose_stamped = self.create_pose_stamped(
            waypoint['x'], waypoint['y'], waypoint.get('yaw', 0.0)
        )
        self.navigate_to_pose(pose_stamped)

    def navigate_to_origin(self):
        origin_pose = self.create_pose_stamped(0.0, 0.0, 0.0)
        self.get_logger().info("导航回原点（0,0,0）")
        self.navigate_to_pose(origin_pose)

def main(args=None):
    rclpy.init(args=args)
    navigator = MultiWaypointNavigator()
    try:
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        if navigator.goal_handle and navigator.goal_handle.accepted:
            navigator.get_logger().info("收到中断，取消当前目标")
            cancel_future = navigator.goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(navigator, cancel_future)
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()




# #!/usr/bin/env python3

# import rclpy
# from rclpy.node import Node
# from rclpy.action import ActionClient
# from geometry_msgs.msg import PoseStamped
# from nav2_msgs.action import NavigateToPose
# from nav_msgs.msg import Odometry
# from tf2_ros import TransformException
# from tf2_ros.buffer import Buffer
# from tf2_ros.transform_listener import TransformListener
# import yaml
# import os
# from ament_index_python.packages import get_package_share_directory
# import time
# from math import atan2, sin, cos, sqrt
# from action_msgs.msg import GoalStatus

# class MultiWaypointNavigator(Node):
#     def __init__(self):
#         super().__init__('multi_waypoint_navigator')
        
#         # Declare parameters
#         self.declare_parameter('waypoints_file', 'waypoints.yaml')
#         self.declare_parameter('position_tolerance', 0.25)
#         self.declare_parameter('orientation_tolerance', 0.5)
#         self.declare_parameter('wait_time_at_waypoint', 5.0)  # 等待时间参数（秒）
        
#         # Get parameters
#         waypoints_file = self.get_parameter('waypoints_file').value
#         self.position_tolerance = self.get_parameter('position_tolerance').value
#         self.orientation_tolerance = self.get_parameter('orientation_tolerance').value
#         self.wait_time_at_waypoint = self.get_parameter('wait_time_at_waypoint').value
        
#         # Load waypoints from YAML file
#         self.waypoints = self.load_waypoints(waypoints_file)
#         self.current_waypoint_index = 0
#         self.is_returning_to_origin = False
#         self.is_navigating = False  # 跟踪导航状态
#         self.is_waiting = False  # 跟踪等待状态
#         self.navigation_cycle_complete = False # 标记一个循环是否完成
        
#         # TF2 listener for transformations
#         self.tf_buffer = Buffer()
#         self.tf_listener = TransformListener(self.tf_buffer, self)
        
#         # Action client for navigation
#         self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
#         # Subscribe to current pose (using odometry as fallback)
#         self.current_pose = None
#         self.odom_subscription = self.create_subscription(
#             Odometry, 
#             'odom', 
#             self.odom_callback, 
#             10)
        
#         # Wait for action server
#         self.get_logger().info("Waiting for navigate_to_pose action server...")
#         if not self.nav_to_pose_client.wait_for_server(timeout_sec=10.0):
#             self.get_logger().error("Action server not available after waiting")
#             return
        
#         self.get_logger().info("Action server detected!")
        
#         # Start navigation after a short delay
#         self.timer = self.create_timer(2.0, self.start_navigation)
        
#         # Track goal handle and timers
#         self.goal_handle = None
#         self.result_future = None
#         self.wait_timer = None
#         self.retry_timer = None
#         self.origin_timer = None
#         self.next_wp_timer = None
#         self.restart_timer = None
#         self.post_origin_failure_timer = None # 新增：处理返回原点失败后的定时器

#     def start_navigation(self):
#         """Start navigation after timer"""
#         if self.timer:
#             self.destroy_timer(self.timer)
#             self.timer = None
#         self.navigate_to_next_waypoint()

#     def load_waypoints(self, waypoints_file):
#         """Load waypoints from YAML configuration file"""
#         # Get the full path to the config file
#         if not waypoints_file.startswith('/'):
#             # Assume it's in the config directory of this package
#             package_share_dir = get_package_share_directory('multi_waypoint_navigator')
#             waypoints_file = os.path.join(package_share_dir, 'config', waypoints_file)
        
#         self.get_logger().info(f"Loading waypoints from: {waypoints_file}")
        
#         try:
#             with open(waypoints_file, 'r') as file:
#                 config = yaml.safe_load(file)
#                 waypoints = config.get('waypoints', [])
#                 self.get_logger().info(f"Loaded {len(waypoints)} waypoints")
#                 return waypoints
#         except Exception as e:
#             self.get_logger().error(f"Failed to load waypoints: {e}")
#             return []

#     def odom_callback(self, msg):
#         """Callback for odometry messages to get current position"""
#         self.current_pose = msg.pose.pose

#     def get_current_pose(self):
#         """Get current robot pose using TF2 transformation from odom to base_link"""
#         try:
#             # Look up the transform from map to base_link
#             transform = self.tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            
#             # Create a PoseStamped with the transform
#             pose_stamped = PoseStamped()
#             pose_stamped.header.stamp = self.get_clock().now().to_msg()
#             pose_stamped.header.frame_id = 'map'
#             pose_stamped.pose.position.x = transform.transform.translation.x
#             pose_stamped.pose.position.y = transform.transform.translation.y
#             pose_stamped.pose.position.z = transform.transform.translation.z
#             pose_stamped.pose.orientation = transform.transform.rotation
            
#             return pose_stamped.pose
#         except TransformException as ex:
#             self.get_logger().warn(f'Could not transform from map to base_link: {ex}')
#             return None

#     def create_pose_stamped(self, x, y, yaw):
#         """Create a PoseStamped message from x, y, yaw"""
#         pose_stamped = PoseStamped()
#         pose_stamped.header.frame_id = 'map'
#         pose_stamped.header.stamp = self.get_clock().now().to_msg()
#         pose_stamped.pose.position.x = x
#         pose_stamped.pose.position.y = y
#         pose_stamped.pose.position.z = 0.0
        
#         # Convert yaw to quaternion
#         pose_stamped.pose.orientation.x = 0.0
#         pose_stamped.pose.orientation.y = 0.0
#         pose_stamped.pose.orientation.z = sin(yaw / 2)
#         pose_stamped.pose.orientation.w = cos(yaw / 2)
        
#         return pose_stamped

#     def navigate_to_pose(self, pose_stamped):
#         """Send a navigation goal to the action server"""
#         # 检查是否已经在导航中
#         if self.is_navigating:
#             self.get_logger().warn("Already navigating, skipping new goal")
#             return
            
#         self.is_navigating = True
        
#         goal_msg = NavigateToPose.Goal()
#         goal_msg.pose = pose_stamped
        
#         self.get_logger().info(f'Navigating to goal: x={pose_stamped.pose.position.x:.2f}, '
#                               f'y={pose_stamped.pose.position.y:.2f}, '
#                               f'yaw={atan2(2*(pose_stamped.pose.orientation.z*pose_stamped.pose.orientation.w), 1-2*(pose_stamped.pose.orientation.z*pose_stamped.pose.orientation.z)):.2f}')
        
#         # Send the goal
#         self.send_goal_future = self.nav_to_pose_client.send_goal_async(
#             goal_msg, 
#             feedback_callback=self.feedback_callback)
#         self.send_goal_future.add_done_callback(self.goal_response_callback)

#     def goal_response_callback(self, future):
#         """Callback for when the goal is accepted or rejected"""
#         self.goal_handle = future.result()
#         if not self.goal_handle.accepted:
#             self.get_logger().info('Goal rejected')
#             self.is_navigating = False
#             # Schedule retry after a short delay using a one-shot timer
#             if self.retry_timer:
#                  self.destroy_timer(self.retry_timer)
#             self.retry_timer = self.create_timer(2.0, self._retry_timer_callback)
#             return
        
#         self.get_logger().info('Goal accepted')
#         self.result_future = self.goal_handle.get_result_async()
#         self.result_future.add_done_callback(self.get_result_callback)

#     def feedback_callback(self, feedback_msg):
#         """Callback for navigation feedback"""
#         # feedback = feedback_msg.feedback
#         # You can add feedback processing here if needed
#         pass

#     def get_result_callback(self, future):
#         """Callback for when the navigation is complete"""
#         result = future.result()
#         status = result.status
        
#         self.is_navigating = False  # 导航结束
        
#         if status == GoalStatus.STATUS_SUCCEEDED:
#             self.get_logger().info(f'Navigation completed successfully')
#             # 到达目标点后等待指定时间
#             self.wait_at_waypoint()
#         else:
#             self.get_logger().warn(f'Navigation failed with status: {status}')
#             # --- 关键修复：区分失败类型 ---
#             if self.is_returning_to_origin:
#                  self.get_logger().warn("Failed to return to origin.")
#                  # 重置返回原点状态
#                  self.is_returning_to_origin = False
#                  # 可以选择重试或停止。这里我们选择停止当前循环并等待重启。
#                  self.navigation_cycle_complete = True
#                  self.current_waypoint_index = 0 # 重置索引
#                  # 使用定时器安全地处理后续逻辑，避免在回调中直接调用
#                  if self.post_origin_failure_timer:
#                      self.destroy_timer(self.post_origin_failure_timer)
#                  self.post_origin_failure_timer = self.create_timer(0.1, self._handle_post_origin_failure)
#             else:
#                 # Retry the current waypoint after a short delay using a one-shot timer
#                 if self.retry_timer:
#                      self.destroy_timer(self.retry_timer)
#                 self.retry_timer = self.create_timer(2.0, self._retry_timer_callback)
            
#     def _handle_post_origin_failure(self):
#         """Helper callback to handle logic after origin return failure."""
#         if self.post_origin_failure_timer:
#             self.destroy_timer(self.post_origin_failure_timer)
#             self.post_origin_failure_timer = None
#         self.get_logger().info("Origin return failed. Waiting to restart cycle.")
#         # 等待一段时间后重新开始 (例如，5秒后)
#         if self.restart_timer:
#             self.destroy_timer(self.restart_timer)
#         self.restart_timer = self.create_timer(5.0, self._restart_navigation_cycle)

            
#     def _retry_timer_callback(self):
#         """Helper callback for retry timer. Destroys timer and retries."""
#         if self.retry_timer:
#             self.destroy_timer(self.retry_timer)
#             self.retry_timer = None
#         self.navigate_to_next_waypoint() # This will handle index checks

#     def wait_at_waypoint(self):
#         """Wait at the current waypoint for the specified time"""
#         if self.is_waiting:
#             self.get_logger().warn("Already waiting, skipping new wait")
#             return
            
#         self.is_waiting = True
        
#         if self.is_returning_to_origin:
#             # 回到原点后等待10秒
#             wait_time = 10.0
#             self.get_logger().info(f'Returned to origin. Waiting {wait_time} seconds...')
#         else:
#              # 在普通航点等待指定时间
#             wait_time = self.wait_time_at_waypoint
#             # --- 修复点：在等待前检查索引范围 ---
#             if 0 <= self.current_waypoint_index < len(self.waypoints):
#                  waypoint_name = self.waypoints[self.current_waypoint_index].get('name', f'waypoint {self.current_waypoint_index+1}')
#             else:
#                  # 如果索引越界（理论上不应发生在此处，但做防御性检查），使用通用名称
#                  waypoint_name = f'waypoint (index {self.current_waypoint_index})'
#             self.get_logger().info(f'Reached {waypoint_name}. Waiting {wait_time} seconds...')
        
#         # --- 修复点：创建一次性定时器等待指定时间 (兼容 Humble) ---
#         if self.wait_timer:
#             self.destroy_timer(self.wait_timer)
#         self.wait_timer = self.create_timer(wait_time, self.wait_completed)

#     def wait_completed(self):
#         """Callback when waiting at a waypoint is completed"""
#         # --- 修复点：手动销毁一次性定时器 (兼容 Humble) ---
#         if self.wait_timer:
#             self.destroy_timer(self.wait_timer)
#             self.wait_timer = None
#         self.is_waiting = False
#         self.waypoint_reached()

#     def waypoint_reached(self):
#         """Handle what happens when a waypoint is reached and waiting is completed"""
#         self.get_logger().debug(f"Handling waypoint reached. Index: {self.current_waypoint_index}, Returning: {self.is_returning_to_origin}, Cycle Complete: {self.navigation_cycle_complete}")

#         # --- 修复点：在处理航点到达时，再次检查状态 ---
#         if self.navigation_cycle_complete:
#             self.get_logger().debug("Navigation cycle complete, waiting for restart trigger.")
#             return # 如果循环已完成，不处理后续航点逻辑

#         if self.is_returning_to_origin:
#             # --- 修改逻辑：回到原点后，标记循环完成 ---
#             self.get_logger().info("Returned to origin. Navigation cycle complete.")
#             self.is_returning_to_origin = False
#             self.navigation_cycle_complete = True
#             self.current_waypoint_index = 0 # 为下一次循环做准备
#             # --- 修改逻辑：等待一段时间后重新开始 (例如，5秒后) ---
#             if self.restart_timer:
#                 self.destroy_timer(self.restart_timer)
#             self.restart_timer = self.create_timer(5.0, self._restart_navigation_cycle)
            
#         else:
#             # --- 修改逻辑：移动到下一个航点 ---
#             self.current_waypoint_index += 1
#             self.get_logger().debug(f"Incremented waypoint index to: {self.current_waypoint_index}")
            
#             if self.current_waypoint_index >= len(self.waypoints):
#                 # 所有航点完成，返回原点
#                 self.get_logger().info('All waypoints completed. Returning to origin...')
#                 self.is_returning_to_origin = True
#                 # --- 修复点：使用一次性定时器调用 navigate_to_origin ---
#                 if self.origin_timer:
#                     self.destroy_timer(self.origin_timer)
#                 self.origin_timer = self.create_timer(0.1, self._go_to_origin_timer_callback)
#             else:
#                 # --- 修复点：使用一次性定时器调用 navigate_to_next_waypoint ---
#                 if self.next_wp_timer:
#                     self.destroy_timer(self.next_wp_timer)
#                 self.next_wp_timer = self.create_timer(0.1, self._go_to_next_wp_timer_callback)

#     def _go_to_origin_timer_callback(self):
#         """Helper callback for origin timer. Destroys timer and calls navigate_to_origin."""
#         if self.origin_timer:
#             self.destroy_timer(self.origin_timer)
#             self.origin_timer = None
#         self.navigate_to_origin()

#     def _go_to_next_wp_timer_callback(self):
#         """Helper callback for next waypoint timer. Destroys timer and calls navigate_to_next_waypoint."""
#         if self.next_wp_timer:
#             self.destroy_timer(self.next_wp_timer)
#             self.next_wp_timer = None
#         self.navigate_to_next_waypoint()

#     def _restart_navigation_cycle(self):
#         """Helper callback for restart timer. Destroys timer and restarts the cycle."""
#         if self.restart_timer:
#             self.destroy_timer(self.restart_timer)
#             self.restart_timer = None
#         self.get_logger().info("Restarting navigation cycle.")
#         self.navigation_cycle_complete = False
#         self.navigate_to_next_waypoint() # 开始新循环

#     def navigate_to_next_waypoint(self):
#         """Navigate to the next waypoint in the list"""
#         # --- 核心修复点：添加索引范围检查 ---
#         # --- 修复点：在导航到下一个航点前，检查循环是否已完成 ---
#         if self.navigation_cycle_complete:
#              self.get_logger().debug("Navigation cycle complete, skipping waypoint navigation.")
#              return

#         if 0 <= self.current_waypoint_index < len(self.waypoints):
#             waypoint = self.waypoints[self.current_waypoint_index]
#             pose_stamped = self.create_pose_stamped(waypoint['x'], waypoint['y'], waypoint.get('yaw', 0.0)) # Default yaw to 0
#             self.navigate_to_pose(pose_stamped)
#         else:
#             # --- 核心修复点：处理索引越界但非返回原点的情况 ---
#             # 这可能发生在循环完成或逻辑错误时。添加日志并避免错误。
#             self.get_logger().warn(f'Waypoint index {self.current_waypoint_index} is out of range (0-{len(self.waypoints)-1}). Current state - Returning: {self.is_returning_to_origin}, Cycle Complete: {self.navigation_cycle_complete}')
#             # 如果循环已完成，可以等待重启信号
#             if self.navigation_cycle_complete and not self.is_returning_to_origin:
#                  self.get_logger().debug("Navigation cycle complete, waiting for restart trigger.")


#     def navigate_to_origin(self):
#         """Navigate back to the origin (0, 0, 0)"""
#         self.get_logger().info("Navigating to origin")
#         origin_pose = self.create_pose_stamped(0.0, 0.0, 0.0)
#         self.navigate_to_pose(origin_pose)

# def main(args=None):
#     rclpy.init(args=args)
#     navigator = MultiWaypointNavigator()
#     try:
#         rclpy.spin(navigator)
#     except KeyboardInterrupt:
#         # 取消当前目标（如果存在）
#         if navigator.goal_handle and navigator.goal_handle.accepted:
#             navigator.get_logger().info("Cancelling current goal due to interrupt")
#             cancel_future = navigator.goal_handle.cancel_goal_async()
#             rclpy.spin_until_future_complete(navigator, cancel_future)
#     finally:
#         navigator.destroy_node()
#         rclpy.shutdown()

# if __name__ == '__main__':
#     main()
