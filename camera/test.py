import cv2
import time
import numpy as np
from ultralytics import YOLO
from mqtt_server import *

mqtt_client = MY_MQTT_CLIENT(topic='camera/data')  # 统一发送到 camera/data
model = YOLO("s3.pt")  # 替换为你的模型路径
# 打开摄像头
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("无法打开摄像头")
    exit()
print("摄像头启动，开始执行任务...")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("摄像头读取失败")
            break

        frame = cv2.resize(frame, (640,640))
        results = model.predict(
            source=frame,  # 直接传入OpenCV的帧数据
            conf=0.5,  # 置信度阈值
            verbose=False  # 关闭冗余输出
        )

        # 获取检测结果并可视化
        annotated_frame = results[0].plot()  # 自动绘制检测框和标签

        send_img_for_mqtt(mqtt_client, annotated_frame,(320, 240),"仪表数值：0")

        # time.sleep(0.1)  # 控制帧率（约10fps）

except KeyboardInterrupt:
    print("\n停止发布")

finally:
    cap.release()
    mqtt_client.client.loop_stop()
    mqtt_client.client.disconnect()







# # script.py
# import cv2
# import time
# import base64
# from mqtt_server import *
#
# mqtt_client = MY_MQTT_CLIENT()
#
# # 打开摄像头
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     print("无法打开摄像头")
#     exit()
# print("摄像头启动，开始执行任务...")
#
# try:
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("摄像头读取失败")
#             break
#
#         # 缩放图像（减小带宽）
#         frame = cv2.resize(frame, (640, 480))
#
#         # 编码为 JPEG
#         _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
#
#         # 转为 Base64 字符串
#         jpg_as_text = base64.b64encode(buffer).decode('utf-8')
#
#         # 发布到 MQTT
#         result = mqtt_client.client.publish(mqtt_client.MQTT_TOPIC, jpg_as_text, qos=0)
#
#         time.sleep(0.1)  # 控制帧率（约10fps）
#
# except KeyboardInterrupt:
#     print("\n🛑 停止发布")
#
# finally:
#     cap.release()
#     mqtt_client.client.loop_stop()  # 停止后台线程
#     mqtt_client.client.disconnect()
#
#
#
#
#
#
#
#
#
#
#
#
#
