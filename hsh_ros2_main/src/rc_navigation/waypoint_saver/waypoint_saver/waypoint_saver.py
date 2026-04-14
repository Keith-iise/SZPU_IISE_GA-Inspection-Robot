#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray
from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
import tf2_ros
import yaml
import os
from geometry_msgs.msg import TransformStamped
import math

class WaypointSaver(Node):
    def __init__(self):
        super().__init__('waypoint_saver')

        # 声明参数：文件保存路径
        self.declare_parameter('save_path', '/home/r2/Desktop/hsh_ros2_main/src/rc_navigation/multi_waypoint_navigator/config/waypoints.yaml')
        self.declare_parameter('min_record_distance', 0.2)

        
        self.save_path = self.get_parameter('save_path').get_parameter_value().string_value
        self.min_record_distance = self.get_parameter('min_record_distance').get_parameter_value().double_value

        # 创建 TF2 监听器
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # 订阅 /serial_topic
        self.subscription = self.create_subscription(
            Int16MultiArray,
            '/serial_topic',
            self.serial_callback,
            10
        )

        # 当前记录的最后一个点
        self.last_recorded_index = 0
        self.last_pose = None  # {'x': x, 'y': y, 'yaw': yaw}

        # 存储所有路径点
        self.waypoints = []
        self.point_count = 1

        # 确保目录存在
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)

        self.get_logger().info(f"Waypoint Saver 启动，保存路径: {self.save_path}")
        self.get_logger().info("等待 /serial_topic 数据...")

    def quaternion_to_yaw(self, qx, qy, qz, qw):
        """将四元数转换为偏航角 (yaw)"""
        siny_cosp = 2 * (qw * qz + qx * qy)
        cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
        return math.atan2(siny_cosp, cosy_cosp)

    def get_robot_pose(self):
        """获取 base_link 在 map 坐标系下的位姿"""
        try:
            now = rclpy.time.Time()
            trans: TransformStamped = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                now,
                timeout=rclpy.duration.Duration(seconds=1.0)
            )

            x = trans.transform.translation.x
            y = trans.transform.translation.y
            qx = trans.transform.rotation.x
            qy = trans.transform.rotation.y
            qz = trans.transform.rotation.z
            qw = trans.transform.rotation.w
            yaw = self.quaternion_to_yaw(qx, qy, qz, qw)

            return {'x': x, 'y': y, 'yaw': yaw}

        except TransformException as ex:
            self.get_logger().warn(f'无法获取 TF 变换: {ex}')
            return None

    def distance_2d(self, p1, p2):
        """计算 2D 平面距离"""
        return math.hypot(p1['x'] - p2['x'], p1['y'] - p2['y'])

    def serial_callback(self, msg):
        # 检查 data 是否有至少 6 个元素
        if len(msg.data) < 6:
            self.get_logger().warn("serial_topic 数据少于6个元素")
            return

        current_index = msg.data[5]  # 第六个元素，索引为5
        

        # 如果为0，不记录
        if current_index == 0:
            return

        # 只有当编号变化时才记录
        if current_index == self.last_recorded_index:
            return

        # 获取机器人当前位姿
        pose = self.get_robot_pose()
        if pose is None:
            self.get_logger().warn("无法获取机器人位姿，跳过记录")
            return

        # 如果是第一个点，直接记录
        if self.last_recorded_index == 0:
            self.save_waypoint(current_index, pose)
            self.last_recorded_index = current_index
            self.last_pose = pose
            return

        # 检查距离是否大于 min_record_distance 米（去抖）
        if self.last_pose and self.distance_2d(pose, self.last_pose) < self.min_record_distance:
            self.get_logger().info(f"点 {current_index} 距离上一个点太近 (<{self.min_record_distance})，跳过")
            return  # 可改为更新上一个点，这里选择跳过

        # 记录新点
        self.save_waypoint(current_index, pose)
        self.last_recorded_index = current_index
        self.last_pose = pose

    def save_waypoint(self, index, pose):
        """保存一个路径点到列表并写入文件"""
        point_name = f"point{self.point_count}"
        waypoint = {
            'x': round(pose['x'], 2),
            'y': round(pose['y'], 2),
            'yaw': round(pose['yaw'], 2),
            'name': point_name
        }
        self.point_count += 1

        # 添加到列表
        self.waypoints.append(waypoint)

        # 写入文件
        data = {'waypoints': self.waypoints}
        try:
            with open(self.save_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)
            self.get_logger().info(f"✅ 已记录点 {point_name}: x={pose['x']:.2f}, y={pose['y']:.2f}, yaw={pose['yaw']:.2f}")
        except Exception as e:
            self.get_logger().error(f"❌ 保存文件失败: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = WaypointSaver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()