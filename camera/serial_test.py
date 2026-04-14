import serial , struct


ser = None
baudrate = 115200
serial_initialized = False
possible_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']


# 自动尝试打开串口
for port in possible_ports:
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        if ser.is_open:
            print(f'成功打开串口: {port}，波特率 {baudrate}')
            serial_initialized = True
            break  # 成功打开后退出循环
    except (serial.SerialException, OSError) as e:
        print(f'无法打开串口 {port}: {e}')
        continue  # 继续尝试下一个端口

# 如果所有端口都失败
if not serial_initialized:
    error_msg = '无法打开任何串口设备，已尝试: ' + ', '.join(possible_ports)
    print(error_msg)






speed = 0
angular = 0

# 限制在 int16 范围内 (-32768 ~ 32767)
speed = max(min(speed, 0x7FFF), -0x8000)
angular = max(min(angular, 0x7FFF), -0x8000)

# 转换为 2 字节（有符号，大端）
speed_bytes = struct.pack('>h', speed)  # > 表示大端，h 表示 int16
angular_bytes = struct.pack('>h', angular)

# 构造数据包
packet = bytes([
    0xCC,
    speed_bytes[0], speed_bytes[1],
    0x00,0x00,
    angular_bytes[0], angular_bytes[1],
    0x01, 0x00,
    0xEE
])

# 发送数据
ser.write(packet)