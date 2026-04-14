import numpy as np
import cv2


def vector_angle(center, point):
    """返回从 center 到 point 的向量角度（弧度）"""
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    return np.arctan2(dy, dx)
def angle_diff_positive(from_angle, to_angle):
    """返回 [0, 2π) 范围内的正向角度差（from → to）"""
    diff = to_angle - from_angle
    return (diff + 2 * np.pi) % (2 * np.pi)

def estimate_gauge_value(frame, results,current_value, min_value=0.0, max_value=10.0,debug=0):
    result = results[0]
    boxes = {}
    img_cx,img_cy = frame.shape[1]//2,frame.shape[0]//2

    for box in result.boxes:
        class_id = int(box.cls.cpu().numpy()[0])
        class_name = result.names[class_id]
        xyxy = box.xyxy[0].cpu().numpy()
        cx = int((xyxy[0] + xyxy[2]) / 2)
        cy = int((xyxy[1] + xyxy[3]) / 2)

        if (class_name == "max" and cx < img_cx) or (class_name == "min" and cx > img_cx) :
            continue
        boxes[class_name] = (cx, cy)
        if debug:
            print(f"检测到 {class_name}: ({cx}, {cy})")

    required = ['min', 'max', 'center', 'tip']
    for name in required:
        if name not in boxes:
            if debug:
                print(f"❌ 缺少检测: {name}")
            return current_value

    center = boxes['center']
    min_pt = boxes['min']
    max_pt = boxes['max']
    tip_pt = boxes['tip']

    # 计算向量角度
    a_min = vector_angle(center, min_pt)
    a_max = vector_angle(center, max_pt)
    a_tip = vector_angle(center, tip_pt)



    # 计算 min → max 的正向弧长（顺时针）
    total_arc = angle_diff_positive(a_min, a_max)  # [0, 2π)


    # 计算 min → tip 的正向弧长
    tip_arc = angle_diff_positive(a_min, a_tip)


    # 如果 tip_arc > total_arc，说明指针超出了范围
    if tip_arc > total_arc:
        if debug:
            print("指针超出 max 范围")
        ratio = 1.0
    else:
        ratio = tip_arc / total_arc

    estimated_value = min_value + ratio * (max_value - min_value)
    # print(f"最终值: {estimated_value:.2f}")

    if debug:
        debug_frame = frame.copy()
        cv2.circle(debug_frame, center, 5, (0, 0, 255), -1)
        cv2.circle(debug_frame, min_pt, 5, (0, 255, 0), -1)
        cv2.circle(debug_frame, max_pt, 5, (0, 255, 0), -1)
        cv2.circle(debug_frame, tip_pt, 5, (255, 0, 0), -1)
        cv2.line(debug_frame, center, tip_pt, (255, 0, 0), 2)

        cv2.putText(debug_frame, f"Value: {estimated_value:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Debug", debug_frame)



    return estimated_value




# def vector_angle(center, point):
#     """返回从 center 到 point 的向量角度（弧度）"""
#     dx = point[0] - center[0]
#     dy = point[1] - center[1]
#     return np.arctan2(dy, dx)
# def angle_diff_positive(from_angle, to_angle):
#     """返回 [0, 2π) 范围内的正向角度差（from → to）"""
#     diff = to_angle - from_angle
#     return (diff + 2 * np.pi) % (2 * np.pi)
#
# def estimate_gauge_value(frame, results, min_value=0.0, max_value=100.0):
#     result = results[0]
#     boxes = {}
#
#     for box in result.boxes:
#         class_id = int(box.cls.cpu().numpy()[0])
#         class_name = result.names[class_id]
#         xyxy = box.xyxy[0].cpu().numpy()
#         cx = int((xyxy[0] + xyxy[2]) / 2)
#         cy = int((xyxy[1] + xyxy[3]) / 2)
#         boxes[class_name] = (cx, cy)
#         print(f"检测到 {class_name}: ({cx}, {cy})")
#
#     required = ['min', 'max', 'center', 'tip']
#     for name in required:
#         if name not in boxes:
#             print(f"❌ 缺少检测: {name}")
#             return None
#
#     center = boxes['center']
#     min_pt = boxes['min']
#     max_pt = boxes['max']
#     tip_pt = boxes['tip']
#
#     # 计算向量角度
#     a_min = vector_angle(center, min_pt)
#     a_max = vector_angle(center, max_pt)
#     a_tip = vector_angle(center, tip_pt)
#
#     print(f"\n角度（弧度）:")
#     print(f"  min:  {a_min:6.2f}")
#     print(f"  max:  {a_max:6.2f}")
#     print(f"  tip:  {a_tip:6.2f}")
#
#     # 计算 min → max 的正向弧长（顺时针）
#     total_arc = angle_diff_positive(a_min, a_max)  # [0, 2π)
#     print(f"  min→max 弧长: {total_arc:6.2f} rad")
#
#     # 计算 min → tip 的正向弧长
#     tip_arc = angle_diff_positive(a_min, a_tip)
#     print(f"  min→tip 弧长: {tip_arc:6.2f} rad")
#
#     # ✅ 关键：如果 tip_arc > total_arc，说明指针超出了范围
#     if tip_arc > total_arc:
#         print("⚠️  指针超出 max 范围")
#         ratio = 1.0
#     else:
#         ratio = tip_arc / total_arc
#
#     print(f"  ratio: {ratio:.3f}")
#
#     estimated_value = min_value + ratio * (max_value - min_value)
#     print(f"  最终值: {estimated_value:.2f}")
#
#     debug_frame = frame.copy()
#     cv2.circle(debug_frame, center, 5, (0, 0, 255), -1)
#     cv2.circle(debug_frame, min_pt, 5, (0, 255, 0), -1)
#     cv2.circle(debug_frame, max_pt, 5, (0, 255, 0), -1)
#     cv2.circle(debug_frame, tip_pt, 5, (255, 0, 0), -1)
#     cv2.line(debug_frame, center, tip_pt, (255, 0, 0), 2)
#
#     cv2.putText(debug_frame, f"Value: {estimated_value:.2f}", (10, 30),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#     cv2.imshow("Debug", debug_frame)
#
#
#     return estimated_value