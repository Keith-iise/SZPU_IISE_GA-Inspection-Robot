import cv2
import base64
import json
import paho.mqtt.client as mqtt


class MY_MQTT_CLIENT:
    def __init__(self, broker='localhost', port=1883, topic='camera/data'):

        # MQTT 配置
        self.MQTT_BROKER = broker
        self.MQTT_PORT = port
        self.MQTT_TOPIC = topic  # 改为更通用的 topic

        # 显式指定 callback_api_version
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

        # 连接 MQTT
        try:
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            self.client.loop_start()  # 启动后台线程处理网络通信
        except Exception as e:
            print(f"MQTT 连接失败: {e}")
            exit()



def send_img_for_mqtt(mqtt_client,frame,size,text):
    # 缩放图像
    frame = cv2.resize(frame, dsize=size)

    # 编码为 JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

    # 转为 Base64 字符串
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')

    # 构造 JSON 数据包
    payload = {
        "image": jpg_as_text,
        "message": str(text)
    }

    # 发布 JSON 数据
    result = mqtt_client.client.publish(
        mqtt_client.MQTT_TOPIC,
        json.dumps(payload),  # 序列化为 JSON 字符串
        qos=0
    )
    # print(result)
