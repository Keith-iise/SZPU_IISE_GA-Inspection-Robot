import cv2
import numpy as np
from ultralytics import YOLO
from Camera.HKCamera import *
from ValueGet import *
import pprint
# 1. 加载训练好的模型（使用best.pt或last.pt）
model = YOLO("s3.pt")  # 替换为你的模型路径





def camera():
    cap = Camera(0)  # 或使用你的 Camera(0)
    result_value = 0
    while True:
        success, frame = cap.read()
        if not success:
            print("摄像头读取失败！")
            break

        results = model.predict(
            source=frame,
            conf=0.1,
            verbose=False
        )

        try:
            # 假设仪表盘范围是 0 ~ 150
            result_value = estimate_gauge_value(frame, results,result_value, min_value=0.0, max_value=100.0)
            print(result_value)
        except Exception as e:
            print("估计失败:", e)
            cv2.imshow("Debug", frame)

        annotated_frame = results[0].plot()
        cv2.imshow("YOLOv8 Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

camera()























# def camera():
#     # 2. 打开摄像头
#     # cap = cv2.VideoCapture(0)  # 0表示默认摄像头，外接摄像头可设为1
#     cap = Camera(0)
#     # 3. 实时检测循环
#     while True:
#         # 读取摄像头帧
#         success, frame = cap.read()
#         if not success:
#             print("摄像头读取失败！")
#             break
#
#         # 使用YOLOv8模型检测当前帧
#         results = model.predict(
#             source=frame,  # 直接传入OpenCV的帧数据
#             conf=0.3,  # 置信度阈值
#             verbose=False  # 关闭冗余输出
#         )
#
#         # 获取检测结果并可视化
#         annotated_frame = results[0].plot()  # 自动绘制检测框和标签
#
#
#         # 显示带检测结果的画面
#         cv2.imshow("YOLOv8 Real-Time Detection", annotated_frame)
#
#         # 按 'q' 退出循环
#         if cv2.waitKey(1) & 0xFF == ord("q"):
#             break
#
#     # 4. 释放资源
#     cap.release()
#     cv2.destroyAllWindows()
#
#
# camera()