#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from expression_msgs.msg import ExpressionMsg
import cv2
import os
import threading
from queue import Queue
import time
from ament_index_python.packages import get_package_share_directory

# 全局队列用于传递表情指令（线程安全）
cmd_queue = Queue(maxsize=1)  # 限制队列大小为1，只保留最新指令
stop_event = threading.Event()
total_pattern = ".jpg"

class ExpressionDisplay(Node):
    def __init__(self):
        super().__init__('expression_display')
        
        # 声明参数
        self.declare_parameter('expression_list', ['开心', '严肃', '警觉', '失落', '正常', '生气', '心动'])
        self.declare_parameter('pattern', ".jpg")
        self.expression_list = self.get_parameter('expression_list').value
        global total_pattern
        total_pattern = self.get_parameter('pattern').value

        # 订阅表情消息
        self.subscriber_ = self.create_subscription(
            ExpressionMsg, 
            "expressions", 
            self.expression_callback, 
            10
        )
        
        # self.timer_ = self.create_timer(0.1, self.timer_callback)


        # 初始表情（确保队列不为空）
        if cmd_queue.empty():
            cmd_queue.put('正常')
        self.get_logger().info("表情显示节点已启动，等待指令...")

    def expression_callback(self, msg):
        """接收表情指令，只保留最新的指令"""
        expression = msg.expression
        if expression in self.expression_list:
            self.get_logger().info(f"收到表情指令: {expression}")
            # 清空队列，放入新指令（队列满时会自动替换）
            with cmd_queue.mutex:
                cmd_queue.queue.clear()
            cmd_queue.put(expression)


def get_sorted_images(expression_path, pattern):
    """获取按数字排序的图片路径列表"""
    if not os.path.exists(expression_path):
        print(f"路径不存在: {expression_path}")
        return []
    
    files = [f for f in os.listdir(expression_path) if f.endswith(pattern)]
    try:
        # 按文件名数字排序（支持001.jpg、1.jpg等格式）
        files.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))
    except (ValueError, IndexError) as e:
        print(f"图片命名错误（需包含数字）: {e}")
        return []
    
    return [os.path.join(expression_path, f) for f in files]


def display_worker():
    """独立线程：处理图片显示和窗口事件（避免阻塞）"""
    # 初始化窗口（单线程创建，避免冲突）
    window_name = "Expression Display"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
    
    # 获取屏幕分辨率（用于最大化窗口）
    screen_width = 1920  # 替换为你的屏幕宽度
    screen_height = 1080  # 替换为你的屏幕高度
    cv2.resizeWindow(window_name, screen_width, screen_height)
    cv2.moveWindow(window_name, 0, 0)  # 窗口置顶左上角

    total_path = os.path.join(
        get_package_share_directory('expression_show'), 
        'resource', 
        'picture'
    )
    current_expression = None
    current_images = []
    frame_idx = 0  # 当前播放的帧索引（避免重复从头播放）

    count = 0

    while not stop_event.is_set():
        # 检查新指令（优先处理）
        if not cmd_queue.empty():
            new_expression = cmd_queue.get()
            cmd_queue.task_done()
            if new_expression != current_expression:
                current_expression = new_expression
                expr_path = os.path.join(total_path, current_expression)
                current_images = get_sorted_images(expr_path, total_pattern)
                frame_idx = 0  # 切换表情时重置帧索引
                print(f"切换到表情: {current_expression}，共{len(current_images)}张图片")

        # 播放图片（确保有图片且未退出）
        if current_images and not stop_event.is_set():
            # 循环播放帧（索引循环）
            img_path = current_images[frame_idx % len(current_images)]
            img = cv2.imread(img_path)

            if img is not None:
                # 调整图片大小以适应窗口（避免拉伸）
                img_resized = cv2.resize(img, (screen_width, screen_height), interpolation=cv2.INTER_AREA)
                # cv2.putText(img_resized, f"问道hen味了", (screen_width//2, screen_height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 5)
                cv2.imshow(window_name, img_resized)
                if frame_idx % len(current_images) == 18 and current_expression=='正常':
                    time.sleep(5)
                

            else:
                print(f"无法读取图片: {img_path}")

            # 关键：处理窗口事件，必须在显示线程中调用
            key = cv2.waitKey(60)  # 60ms延迟（约16fps）
            if key & 0xFF == ord('q') or key == 27:  # ESC或q退出
                stop_event.set()
                break

            frame_idx += 1
        else:
            # 无图片或等待指令时，短暂休眠释放CPU
            time.sleep(0.1)

    # 退出时清理窗口
    cv2.destroyAllWindows()


def main():
    # 解决Wayland兼容性问题（强制使用X11后端）
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    os.environ["DISPLAY"] = ":0"  # 确保使用正确的显示器

    rclpy.init()
    node = ExpressionDisplay()
    
    # 启动显示线程（独立线程处理窗口，避免与ROS2冲突）
    display_thread = threading.Thread(target=display_worker, daemon=True)
    display_thread.start()

    try:
        rclpy.spin(node)  # ROS2节点主循环
    except KeyboardInterrupt:
        pass
    finally:
        # 优雅退出：设置停止信号→等待线程结束→清理资源
        stop_event.set()
        display_thread.join(timeout=2.0)  # 等待2秒确保线程退出
        node.destroy_node()
        rclpy.shutdown()
        print("程序已退出")

if __name__ == '__main__':
    main()






# #!//usr/bin/bin/python3
# import rclpy
# from rclpy.node import Node
# from expression_msgs.msg import ExpressionMsg
# import cv2
# import os
# import threading
# from queue import Queue
# import time
# from ament_index_python.packages import get_package_share_directory

# # 全局队列用于传递表情指令
# cmd_queue = Queue()
# stop_event = threading.Event()  # 退出事件
# total_pattern = ".jpg"
# class ExpressionDisplay(Node):
#     def __init__(self):
#         super().__init__('expression_display')
        
#         # 声明参数
#         self.declare_parameter('expression_list', ['开心', '严肃', '警觉', '失落', '正常', '生气', '心动'])
#         self.declare_parameter('pattern', ".jpg")
#         self.expression_list = self.get_parameter('expression_list').value
#         total_pattern = self.get_parameter('pattern').value

#         # 订阅表情消息
#         self.subscriber_ = self.create_subscription(
#             ExpressionMsg, 
#             "expressions", 
#             self.expression_callback, 
#             10
#         )
        
#         # 初始表情
#         cmd_queue.put('正常')
#         self.get_logger().info("表情显示节点已启动，等待指令...")

#     def expression_callback(self, msg):
#         """接收表情指令，只保留最新的指令"""
#         expression = msg.expression
#         if expression in self.expression_list:
#             self.get_logger().info(f"收到表情指令: {expression}")
#             # 清空队列，只保留最新指令
#             while not cmd_queue.empty():
#                 cmd_queue.get()
#                 cmd_queue.task_done()
#             cmd_queue.put(expression)
#         # else:
#         #     self.get_logger().warn(f"无效表情: {expression}，忽略")

# def get_sorted_images(expression_path, pattern):
#     """获取按数字排序的图片路径列表"""
#     if not os.path.exists(expression_path):
#         # print(f"路径不存在: {expression_path}")
#         return []
    
#     # 筛选指定格式的文件并按数字排序
#     files = [f for f in os.listdir(expression_path) if f.endswith(pattern)]
#     try:
#         files.sort(key=lambda x: int(os.path.splitext(x)[0]))  # 按文件名数字排序
#     except (ValueError, IndexError):
#         # print(f"图片命名错误（需数字命名）: {expression_path}")
#         return []
    
#     return [os.path.join(expression_path, f) for f in files]


# window_name = "Expression Display"
# cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # 允许调整窗口大小
# def display_images(expression, image_paths):
#     """循环显示指定表情的所有图片，直到收到新指令"""
#     while not stop_event.is_set():
        
#         for img_path in image_paths:
            
#             if not cmd_queue.empty():
#                 return
            
#             img = cv2.imread(img_path)
#             if img is not None:
#                 cv2.imshow("Expression Display", img)
#                 cv2.setWindowProperty(
#                 window_name, 
#                 cv2.WND_PROP_FULLSCREEN, 
#                 cv2.WINDOW_FULLSCREEN  # 开启全屏（值为1）
#             )
#             else:
#                 print(f"无法读取图片: {img_path}")
            
            
#             if cv2.waitKey(60) & 0xFF == ord('q'):
#                 stop_event.set()
#                 return
        
        
#         if not cmd_queue.empty():
#             return
        
        
#         time.sleep(0.1)

# def display_worker():
#     """显示线程：处理表情切换和图片播放"""
#     total_path = os.path.join(get_package_share_directory('expression_show'), 'resource', 'picture')
#     current_expression = None
#     current_images = []

#     while not stop_event.is_set():
#         # 检查是否有新指令
#         if not cmd_queue.empty():
#             new_expression = cmd_queue.get()
#             cmd_queue.task_done()

#             # 只有当新表情与当前表情不同时才切换
#             if new_expression != current_expression:
#                 current_expression = new_expression
#                 # 获取新表情的图片路径
#                 expr_path = os.path.join(total_path, current_expression)
#                 current_images = get_sorted_images(expr_path, total_pattern)  # 使用固定格式或参数
#                 # if current_images:
#                 #     print(f"开始显示表情: {current_expression}（{len(current_images)}张图片）")
#                 # else:
#                 #     print(f"表情 {current_expression} 无有效图片")
        
#         # 播放当前表情的图片（确保有图片且未退出）
#         if current_images and not stop_event.is_set():
#             display_images(current_expression, current_images)
#         else:
#             # 无图片或等待指令时休眠
#             time.sleep(0.1)

# def main():
#     # 解决Wayland兼容性问题
#     os.environ["QT_QPA_PLATFORM"] = "xcb"
    
#     # 初始化ROS2
#     rclpy.init()
#     node = ExpressionDisplay()
    
    
    
#     # 启动显示线程
#     display_thread = threading.Thread(target=display_worker, daemon=True)
#     display_thread.start()

#     try:
#         # 运行节点
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         # 优雅退出
#         stop_event.set()
#         node.destroy_node()
#         rclpy.shutdown()
#         cv2.destroyAllWindows()
#         print("程序退出")

# if __name__ == '__main__':
#     main()






# #!/usr/bin/python3
# import rclpy
# from rclpy.node import Node
# from expression_msgs.msg import ExpressionMsg
# import cv2
# import os
# import threading
# from queue import Queue
# import time
# from ament_index_python.packages import get_package_share_directory

# # 全局队列和退出事件
# cmd_queue = Queue()
# stop_event = threading.Event()

# class OLEDControl(Node):
#     def __init__(self):
#         super().__init__('expression_show')
#         self.declare_parameter('expression_list', ['开心', '严肃', '警觉', '失落', '正常', '生气', '心动'])
#         self.declare_parameter('pattern', ".jpg")
#         self.expression_list = self.get_parameter('expression_list').value
#         self.pattern = self.get_parameter('pattern').value
#         self.subscriber_ = self.create_subscription(
#             ExpressionMsg, "expressions", self.get_expression, 10
#         )
#         cmd_queue.put(('正常', self.pattern))  # 初始指令
#         self.get_logger().info("节点启动，等待表情指令...")

#     def get_expression(self, msg):
#         expression = msg.expression
#         if expression in self.expression_list:
#             self.get_logger().info(f"收到表情: {expression}")
#             while not cmd_queue.empty():
#                 cmd_queue.get()
#                 cmd_queue.task_done()
#             cmd_queue.put((expression, self.pattern))

# def get_sorted_files(expression_path, pattern):
#     if not os.path.exists(expression_path):
#         print(f"路径不存在: {expression_path}")
#         return []
#     files = [f for f in os.listdir(expression_path) if f.endswith(pattern)]
#     try:
#         files.sort(key=lambda x: int(os.path.splitext(x)[0]))
#     except:
#         print(f"文件名格式错误: {expression_path}")
#         return []
#     return files

# def normal_show(expression_path, q, pattern):
#     files = get_sorted_files(expression_path, pattern)
#     if not files:
#         return
#     # 限制最大循环次数（避免无限循环）
#     max_loop = 5  # 最多循环5次
#     loop_count = 0
#     while not stop_event.is_set() and loop_count < max_loop:
#         if not q.empty():  # 有新指令立即退出
#             return
#         for file in files:
#             if not q.empty() or stop_event.is_set():
#                 return
#             img = cv2.imread(os.path.join(expression_path, file))
#             if img is not None:
#                 cv2.imshow("face", img)
#             if cv2.waitKey(30) & 0xFF == ord('q'):
#                 stop_event.set()
#                 return
#         loop_count += 1
#         time.sleep(0.1)
#     # 循环结束后主动检查新指令，无指令则重新进入循环
#     if not q.empty():
#         return
#     else:
#         normal_show(expression_path, q, pattern)  # 重新开始循环

# def other_show(expression_path, expression, pattern, state_lock, q):
#     global first_show, final_show, now_expression
#     with state_lock:
#         current_first = first_show
#         current_final = final_show
#         current_expr = now_expression

#     files = get_sorted_files(expression_path, pattern)
#     if not files:
#         return
#     total = len(files)
#     transition_count = min(5, total//2)  # 减少过渡图片数量，加快流程
#     if total < 2:
#         print(f"图片不足: {expression}")
#         return

#     # 过渡阶段：仅执行一次，完成后立即退出
#     if current_final and current_expr != expression and not stop_event.is_set():
#         print(f"切换到{expression}")
#         for file in files[-transition_count:]:
#             if stop_event.is_set() or not q.empty():
#                 return
#             img = cv2.imread(os.path.join(expression_path, file))
#             if img is not None:
#                 cv2.imshow("face", img)
#             if cv2.waitKey(30) & 0xFF == ord('q'):
#                 stop_event.set()
#                 return
#         with state_lock:
#             first_show = True
#             final_show = False
#             now_expression = expression
#         return  # 过渡完成后必须退出

#     # 正常阶段：添加超时机制
#     if current_first and not stop_event.is_set():
#         start_time = time.time()
#         timeout = 5  # 5秒无新指令则重置状态，避免卡死
#         for file in files[:-transition_count]:
#             # 超时或有新指令则退出
#             if stop_event.is_set() or not q.empty() or (time.time() - start_time) > timeout:
#                 with state_lock:
#                     first_show = True  # 超时重置
#                 return
#             img = cv2.imread(os.path.join(expression_path, file))
#             if img is not None:
#                 cv2.imshow("face", img)
#             if cv2.waitKey(30) & 0xFF == ord('q'):
#                 stop_event.set()
#                 return
#         # 正常阶段结束后，强制检查新指令
#         with state_lock:
#             final_show = True
#             first_show = False
#         # 若无新指令，短暂休眠后重新检查状态（避免死锁）
#         time.sleep(0.1)
#         if q.empty():
#             other_show(expression_path, expression, pattern, state_lock, q)
#         return

# def picture_process(q):
#     total_path = os.path.join(get_package_share_directory('expression_show'), 'resource', 'picture')
#     state_lock = threading.Lock()
#     global first_show, final_show, now_expression
#     with state_lock:
#         first_show = True
#         final_show = False
#         now_expression = "正常"

#     while not stop_event.is_set():
#         if q.empty():
#             time.sleep(0.05)
#             continue
#         current_expr, current_pat = q.get()
#         q.task_done()
#         expr_path = os.path.join(total_path, current_expr)
#         if not os.path.exists(expr_path):
#             print(f"路径不存在: {expr_path}")
#             continue

#         if current_expr == '正常':
#             normal_show(expr_path, q, current_pat)
#         else:
#             other_show(expr_path, current_expr, current_pat, state_lock, q)

# def main():
#     os.environ["QT_QPA_PLATFORM"] = "xcb"
#     rclpy.init()
#     node = OLEDControl()
#     picture_thread = threading.Thread(target=picture_process, args=(cmd_queue,), daemon=True)
#     picture_thread.start()
#     try:
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         stop_event.set()
#         node.destroy_node()
#         rclpy.shutdown()
#         cv2.destroyAllWindows()

# if __name__ == '__main__':
#     main()






# #!/usr/bin/python3
# import rclpy
# from rclpy.node import Node
# from expression_msgs.msg import ExpressionMsg
# import cv2
# import os
# import threading
# from queue import Queue
# import time
# from ament_index_python.packages import get_package_share_directory
# total_path = os.path.join(get_package_share_directory('expression_show'),'resource','picture')
# pattern = ".jpg"
# expression_list = ['开心', '严肃', '警觉', '失落', '正常', '生气', '心动']

# # 全局队列用于传递表情指令
# input_queue = Queue()
# input_queue.put('正常')  # 初始表情

# # 全局状态变量
# first_show = True
# final_show = False
# now_expression = ""
# stop_event = threading.Event()  # 用于优雅退出的事件

# class OLEDControl(Node):
#     def __init__(self):
#         super().__init__('oled_control')
#         # 订阅表情消息
#         self.subscriber_ = self.create_subscription(
#             ExpressionMsg, 
#             "expressions", 
#             self.get_expression, 
#             10
#         )
#         self.get_logger().info("OLED控制节点已启动，等待表情消息...")

#     def get_expression(self, msg):
#         """处理接收到的表情消息，放入队列"""
#         expression = msg.expression
#         if expression in expression_list:
#             self.get_logger().info(f"收到表情指令: {expression}")
#             # 清空旧指令，只保留最新的
#             while not input_queue.empty():
#                 input_queue.get()
#                 input_queue.task_done()
#             input_queue.put(expression)
#         else:
#             self.get_logger().warn(f"无效表情指令: {expression}，忽略")

# def get_sorted_files(expression_path):
#     """获取按数字排序的图片文件列表"""
#     if not os.path.exists(expression_path):
#         print(f"路径不存在：{expression_path}")
#         return []
#     files = [f for f in os.listdir(expression_path) if f.endswith(pattern)]
#     try:
#         files.sort(key=lambda x: int(os.path.splitext(x)[0]))
#     except (ValueError, IndexError):
#         print(f"图片文件名格式错误（需数字命名）：{expression_path}")
#         return []
#     return files

# def normal_show(expression_path, q1):
#     """正常表情：循环显示，检查新指令"""
#     files = get_sorted_files(expression_path)
#     if not files:
#         return
#     while not stop_event.is_set() and q1.empty():
#         for file in files:
#             if not q1.empty():
#                 return
#             img_path = os.path.join(expression_path, file)
#             img = cv2.imread(img_path)
#             if img is None:
#                 print(f"无法读取图片：{img_path}")
#                 continue
#             cv2.imshow("face", img)
#             if cv2.waitKey(50) & 0xFF == ord('q') or stop_event.is_set():
#                 stop_event.set()
#                 return
#         time.sleep(0.1)

# def other_show(expression_path, expression):
#     """其他表情：分阶段显示"""
#     global first_show, final_show, now_expression
#     files = get_sorted_files(expression_path)
#     if not files:
#         return
#     total = len(files)
#     if total < 10:
#         print(f"表情 {expression} 图片数量不足（至少需要10张）")
#         return

#     # 表情切换时显示过渡部分
#     if final_show and now_expression != expression and not stop_event.is_set():
#         print(f"切换到{expression}表情，过渡中...")
#         for file in files[-10:]:
#             if stop_event.is_set():
#                 return
#             img = cv2.imread(os.path.join(expression_path, file))
#             if img is None:
#                 continue
#             cv2.imshow("face", img)
#             if cv2.waitKey(50) & 0xFF == ord('q'):
#                 stop_event.set()
#                 return
#         first_show = True
#         final_show = False
#         now_expression = expression

#     # 正常显示阶段
#     if first_show and not stop_event.is_set():
#         for file in files[:-10]:
#             if stop_event.is_set():
#                 return
#             img = cv2.imread(os.path.join(expression_path, file))
#             if img is None:
#                 continue
#             cv2.imshow("face", img)
#             if cv2.waitKey(50) & 0xFF == ord('q'):
#                 stop_event.set()
#                 return
#         final_show = True
#         first_show = False

# def picture_process(q1):
#     """处理图片显示的线程"""
#     current_expression = None
#     while not stop_event.is_set():
#         if not q1.empty():
#             current_expression = q1.get()
#             q1.task_done()
        
#         if current_expression:
#             expression_path = os.path.join(total_path, current_expression)
#             if current_expression == '正常':
#                 normal_show(expression_path, q1)
#             else:
#                 other_show(expression_path, current_expression)
#         else:
#             time.sleep(0.1)

# def main():
#     # 解决Wayland兼容性问题
#     os.environ["QT_QPA_PLATFORM"] = "xcb"
    
#     # 初始化ROS2
#     rclpy.init()
#     oled_control = OLEDControl()

#     # 启动图片显示线程
#     picture_thread = threading.Thread(target=picture_process, args=(input_queue,), daemon=True)
#     picture_thread.start()

#     try:
#         # 运行ROS2节点
#         rclpy.spin(oled_control)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         # 优雅退出
#         stop_event.set()
#         oled_control.destroy_node()
#         rclpy.shutdown()
#         cv2.destroyAllWindows()
#         print("程序退出")

