import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header
import numpy as np
import open3d as o3d
import struct


class PCDPublisher(Node):
    def __init__(self):
        super().__init__('pcd_publisher')
        self.publisher_ = self.create_publisher(PointCloud2, '/cloud_pcd', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)  # 每秒发布一次

        # 加载 PCD 文件
        self.pcd = o3d.io.read_point_cloud("/home/hsh/workspase/new_fast_lio/test.pcd")  # 替换为你的路径
        self.get_logger().info("Loaded PCD file with %d points." % len(self.pcd.points))

    def timer_callback(self):
        cloud_msg = self.convert_to_pointcloud2(self.pcd)
        self.publisher_.publish(cloud_msg)
        self.get_logger().info("Published point cloud.")

    def convert_to_pointcloud2(self, pcd):
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = "base_link"  # 确保和 octomap_server 的 frame_id 一致

        points = np.asarray(pcd.points)

        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]

        height = 1
        width = len(points)
        point_step = 16  # x, y, z (4 bytes each) + padding (4 bytes)
        row_step = point_step * width
        data = []

        for point in points:
            data += list(struct.pack('<ffff', point[0], point[1], point[2], 0.0))  # xyz + padding

        cloud_msg = PointCloud2(
            header=header,
            height=height,
            width=width,
            fields=fields,
            is_bigendian=False,
            point_step=point_step,
            row_step=row_step,
            data=np.array(data, dtype=np.uint8).tobytes(),
            is_dense=True
        )

        return cloud_msg


def main(args=None):
    rclpy.init(args=args)
    node = PCDPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()