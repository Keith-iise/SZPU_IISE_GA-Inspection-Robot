#!/usr/bin/env python3

import rclpy
import serial
import struct
import time
import threading
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int16MultiArray, MultiArrayDimension,Int16


class CmdVelSubscriber(Node):
    def __init__(self):
        super().__init__('cmd_vel_subscriber')

        # 参数配置
        # self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('linear_scale', 1000.0)  # m/s -> mm/s
        self.declare_parameter('angular_scale', 1000.0)  # rad/s -> milli rad/s or deg/s ?
        self.declare_parameter('train_scale', 1000.0)  # rad/s -> milli rad/s or deg/s ?
        self.declare_parameter('angle_run', 100.0)  # rad/s -> milli rad/s or deg/s ?
        

        # port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        self.linear_scale = self.get_parameter('linear_scale').get_parameter_value().double_value
        self.angular_scale = self.get_parameter('angular_scale').get_parameter_value().double_value
        self.train_scale = self.get_parameter('train_scale').get_parameter_value().double_value
        self.angle_run = self.get_parameter('angle_run').get_parameter_value().double_value

        # === 新增：初始化 plane 和 light 默认值 ===
        self.current_plane = 0x01  # 默认值
        self.current_light = 0x01  # 默认值


        # 串口部分
        self.ser = None
        self.serial_initialized = False
        # possible_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']
        possible_ports = ['/dev/base']

        # 自动尝试打开串口
        for port in possible_ports:
            try:
                self.ser = serial.Serial(port, baudrate, timeout=1)
                if self.ser.is_open:
                    self.get_logger().info(f'成功打开串口: {port}，波特率 {baudrate}')
                    self.serial_initialized = True
                    break  # 成功打开后退出循环
            except (serial.SerialException, OSError) as e:
                self.get_logger().debug(f'无法打开串口 {port}: {e}')
                continue  # 继续尝试下一个端口

        # 如果所有端口都失败
        if not self.serial_initialized:
            error_msg = '无法打开任何串口设备，已尝试: ' + ', '.join(possible_ports)
            self.get_logger().error(error_msg)
            raise

        
        # === 新增：创建发布者 ===
        self.serial_publisher = self.create_publisher(Int16MultiArray, '/serial_topic', 10)

        # === 新增：启动串口读取线程 ===
        self.read_thread = threading.Thread(target=self.read_serial_data, daemon=True)
        self.read_thread.start()
        

        # 订阅 /cmd_vel 话题
        self.subscription = self.create_subscription(
            Twist,           # 消息类型
            '/cmd_vel',      # 话题名称
            self.listener_callback,  # 回调函数
            10               # QoS profile depth
        )
         # === 新增：订阅 /light 和 /plane ===
        self.light_subscription = self.create_subscription(
            Int16, 'light', self.light_callback, 10
        )
        self.plane_subscription = self.create_subscription(
            Int16, 'plane', self.plane_callback, 10
        )


        self.get_logger().info("正在监听 /cmd_vel 话题...")

    
    def light_callback(self, msg):
        # 确保值是 uint8 范围（0~255），虽然 Int16 可能更大，但协议只用低8位
        self.current_light = int(msg.data) & 0xFF
        # self.get_logger().debug(f"更新 light: {self.current_light:#04x}")

    def plane_callback(self, msg):
        self.current_plane = int(msg.data) & 0xFF
        # self.get_logger().debug(f"更新 plane: {self.current_plane:#04x}")


    def listener_callback(self, msg):
        # # 提取线速度和角速度
        # linear_x = msg.linear.x
        # angular_z = msg.angular.z

        # 提取线速度和角速度
        vx = msg.linear.x
        wz = msg.angular.z
        # vy = msg.linear.y
        vy = msg.linear.y
        

        speed = vx * self.linear_scale
        translate = vy * self.train_scale
        angular = wz * self.angular_scale

        if abs(angular) > self.angle_run:
            speed = 0
        # else:
        #     angular = 0

        # 缩放并转换为整数（int16）
        speed = int(speed)
        angular = int(angular)
        translate = int(translate)

        # 限制在 int16 范围内 (-32768 ~ 32767)
        speed = max(min(speed, 0x7FFF), -0x8000)
        angular = max(min(angular, 0x7FFF), -0x8000)
        translate = max(min(translate, 0x7FFF), -0x8000)

        # 转换为 2 字节（有符号，大端）
        speed_bytes = struct.pack('>h', speed)  # > 表示大端，h 表示 int16
        angular_bytes = struct.pack('>h', angular)
        translate_bytes = struct.pack('>h', translate)

        # 构造数据包
        packet = bytes([
            0xCC,
            speed_bytes[0], speed_bytes[1],
            translate_bytes[0], translate_bytes[1],
            angular_bytes[0], angular_bytes[1],
            self.current_plane, self.current_light,
            0xEE
        ])

        # 发送数据
        self.ser.write(packet)
        self.get_logger().debug(f'发送数据包: {packet.hex()}')
        # try:
        #     self.ser.write(packet)
        #     self.get_logger().debug(f'发送数据包: {packet.hex()}')
        # except Exception as e:
        #     self.get_logger().error(f'串口写入失败: {e}')


        # 打印出来
        self.get_logger().info(f'接收到速度指令: 线速度 x={speed:.2f},向速度 y={translate:.2f}, 角速度 z={angular:.2f}')

    def read_serial_data(self):
        """
        从串口读取数据，格式: 0xEE + 6 uint8 + 0xCC
        解析中间 6 个字节，发布到 /serial_topic
        """
        buffer = bytearray()
        count = 1

        while rclpy.ok():
            try:

                
                # 读取可用数据
                data = self.ser.read(8)
                

                # # 查找帧头 0xEE
                # while len(buffer) > 0 and buffer[0] != 0xEE:
                #     buffer.pop(0)  
                if not data or data[0] != 0xEE or data[-1] != 0xCC:
                    continue

                # self.get_logger().info(f'data: {data}')


                
                data_bytes = data[1:7]  

                # 转成整数列表
                values = list(data_bytes)
                
                
                values[-1] =  count

                # 创建并发布消息
                msg = Int16MultiArray()
                msg.data = values

                dim = MultiArrayDimension()
                dim.label = "serial_data"
                dim.size = 6
                dim.stride = 6
                msg.layout.dim = [dim]
                msg.layout.data_offset = 0

                self.serial_publisher.publish(msg)
                self.get_logger().info(f'发布串口数据: {values}')
                count += 1

                # 小延时，避免 CPU 占用过高
                # time.sleep(0.01)

            except Exception as e:
                self.get_logger().error(f'读取串口数据失败: {e}')
                break

        # 清理
        if self.ser.is_open:
            self.ser.close()




def main(args=None):
    rclpy.init(args=args)

    cmd_vel_subscriber = CmdVelSubscriber()

    try:
        rclpy.spin(cmd_vel_subscriber)
    except KeyboardInterrupt:
        pass

    # 清理资源
    cmd_vel_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()