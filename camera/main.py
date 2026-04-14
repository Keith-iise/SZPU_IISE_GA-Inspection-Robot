from ultralytics import YOLO
from Camera.HKCamera import *
from mqtt_server import *
from ValueGet import *
mqtt_client = MY_MQTT_CLIENT(topic='camera/data')  # 统一发送到 camera/data
model = YOLO("s3.pt")  # 替换为你的模型路径
# 打开摄像头
# cap = cv2.VideoCapture(0)
cap = Camera(0)
print("摄像头启动，开始执行任务...")
value = 0.00
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("摄像头读取失败")
            break

        # frame = cv2.resize(frame, (640,640))
        results = model.predict(
            source=frame,  # 直接传入OpenCV的帧数据
            conf=0.22,  # 置信度阈值
            verbose=False  # 关闭冗余输出
        )
        # print(results)
        # 获取检测结果并可视化
        value = estimate_gauge_value(frame, results,value, min_value=0.0, max_value=10.0)
        # print(value)

        send_img_for_mqtt(mqtt_client, frame,(320, 240),f"仪表数值：{value:.2f}")

        # time.sleep(0.1)  # 控制帧率（约10fps）

except KeyboardInterrupt:
    print("\n停止发布")

finally:
    cap.release()
    mqtt_client.client.loop_stop()
    mqtt_client.client.disconnect()






# import cv2
# import time
#
# from mqtt_server import *
#
# mqtt_client = MY_MQTT_CLIENT(topic='camera/data')  # 统一发送到 camera/data
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
#         send_img_for_mqtt(mqtt_client, frame,(160, 120),"你好，node-red")
#
#         time.sleep(0.1)  # 控制帧率（约10fps）
#
# except KeyboardInterrupt:
#     print("\n🛑 停止发布")
#
# finally:
#     cap.release()
#     mqtt_client.client.loop_stop()
#     mqtt_client.client.disconnect()


