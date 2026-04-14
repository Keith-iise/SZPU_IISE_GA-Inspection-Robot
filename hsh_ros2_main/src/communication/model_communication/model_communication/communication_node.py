from openai import OpenAI
import os
import tempfile
import asyncio
from playsound import playsound
import edge_tts
import json
import pyaudio
from vosk import Model, KaldiRecognizer  
import rclpy
from rclpy.node import Node
from expression_msgs.msg import ExpressionMsg
import re
from ament_index_python.packages import get_package_share_directory
import requests
from dashscope import MultiModalConversation

# 配置参数
api_key = "sk-52ef118f5c6d40ac9363b9aacd7829e8"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
model = "qwen3-max"
MODEL_PATH = os.path.join(get_package_share_directory('model_communication'), 'resource', "vosk-model-small-cn-0.22")

class My_client(OpenAI):
    def __init__(self):
        super().__init__(api_key=api_key, base_url=base_url)
        self.model = model
        self.modalities = ["text"]
        self.stream = True
        self.stream_options = {"include_usage": True}
        self.max_tokens = 18
        self.top_p = 0.9
        self.temperature = 1.9
        self.top_k = 20
        self.enable_thinking = False
        self.thinking_budget = 100

        # 语音相关参数（dashscope TTS）
        self.audio_model = "qwen-tts"
        self.voice = "Cherry"
        self.language_type = "Chinese"

    def communication(self, input_msgs):
        messages = [
            {"role": "system", "content": """
             你是一个机器人，名叫小智，回答一定要简短，回复时一定要在句尾用()添加文字描述的表情，目前只能括号内只能有这几个文字描述:(开心,严肃,警觉,失落,正常,生气,心动),
             不要出现除了逗号句号括号以外的字符,当有人问你是谁时，请回答（您好,我是深圳职业技术大学智能科学与工程研究院研发的智能巡检机器人，能定时巡逻、读取仪表、语音交互、
             夜间抓拍，还能识别火情并自动灭火，是园区安全的智能守护者！),记住一定要加表情(开心,严肃,警觉,失落,正常,生气,心动)"""},
            {"role": "user", "content": input_msgs}
        ]
        return super().chat.completions.create(
            model=self.model,
            modalities=self.modalities,
            stream=self.stream,
            stream_options=self.stream_options,
            messages=messages,
        )

def get_message(completion):
    output_msg = ''
    for chunk in completion:
        if chunk.choices:
            content = chunk.choices[0].delta.content or ""
            output_msg += content
        elif hasattr(chunk, 'usage') and chunk.usage:
            print(f"Token使用:{chunk.usage.total_tokens}")
    return output_msg

class SaveWave:
    def __init__(self, model_path):
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192
        )
        self.stream.start_stream()

    def listen(self):
        print("正在监听...（说话后停顿一下，会自动识别）")
        while True:
            data = self.stream.read(4096, exception_on_overflow=False)
            if len(data) == 0:
                print("未检测到音频输入")
                break
            if self.rec.AcceptWaveform(data):
                result_dict = json.loads(self.rec.Result())
                text = result_dict.get("text", "").strip()
                if text:
                    return text
        return None

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        print("资源已释放（麦克风关闭）")

def play_audio_from_response(client, text):
    """修复：用临时文件+playsound播放，自动适配采样率"""
    try:
        # 调用dashscope TTS生成音频
        response = MultiModalConversation.call(
            model=client.audio_model,
            api_key=api_key,
            text=text,
            voice=client.voice,
            language_type=client.language_type
        )
        if response.status_code != 200:
            return f"API调用失败：状态码{response.status_code}，信息{response.message}"

        # 下载音频并保存为临时文件
        audio_url = response.output.audio.url
        audio_data = requests.get(audio_url).content
        
        # 创建临时wav文件（自动删除）
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(audio_data)

        # 播放音频（playsound自动处理采样率）
        playsound(temp_filename)
        return True
    except Exception as e:
        return f"播放失败：{str(e)}"
    finally:
        # 确保临时文件被删除
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)

def get_message2(client, full_text):
    if full_text:
        print(f"完整回复：{full_text}")
        result = play_audio_from_response(client, full_text)
        if result is not True:
            print(result)
    return full_text

def text_to_speech(text):
    """备用播放方式（edge-tts），保留原逻辑"""
    async def _generate_audio(text, temp_filename):
        communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoyiNeural")
        await communicate.save(temp_filename)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_filename = temp_file.name
    try:
        asyncio.run(_generate_audio(text, temp_filename))
        playsound(temp_filename)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

class VoiceAssistant(Node):
    def __init__(self, node_name):
        super().__init__(node_name)
        self.client = My_client()
        self.asr = SaveWave(MODEL_PATH)
        self.get_logger().info("=== 语音助手 ===")
        self.publisher_ = self.create_publisher(ExpressionMsg, "expressions", 10)
    
    def speech_run(self):
        while rclpy.ok():
            msg = ExpressionMsg()
            print("(请说话)你:", end='')
            recognized_text = self.asr.listen()
            print(recognized_text)
            
            # 退出逻辑
            if recognized_text and any(keyword in recognized_text for keyword in ["退出", "quit", "exit"]):
                self.get_logger().info("=== 对话结束 ===")
                break
            if not recognized_text or not recognized_text.strip():
                continue
            
            # 模型交互
            response = get_message(self.client.communication(recognized_text))
            # 播放语音（使用修复后的播放函数）
            get_message2(self.client, response[:-4])  # 截取括号前的文本
            
            # 发布表情消息
            msg.stamp = self.get_clock().now().to_msg()
            msg.expression = self.get_expression(response)
            self.get_logger().info(f"result:{msg.expression}")
            self.get_logger().info(f"模型回复：{response}")
            self.publisher_.publish(msg)

    def run(self):
        while rclpy.ok():
            msg = ExpressionMsg()
            user_input = input("你: ")
            if any(keyword in user_input for keyword in ["退出", "quit", "exit"]):
                self.get_logger().info("=== 对话结束 ===")
                break
            if not user_input.strip():
                continue
            
            response = get_message(self.client.communication(user_input))
            text_to_speech(response[:-4])
            
            msg.stamp = self.get_clock().now().to_msg()
            msg.expression = self.get_expression(response)
            self.get_logger().info(f"result:{msg.expression}")
            self.get_logger().info(f"模型回复：{response}")
            self.publisher_.publish(msg)

    def get_expression(self, res):
        pattern = r"\((.*?)\)"
        result = re.findall(pattern, res)
        return result[0] if result else "unknown"

def main():
    rclpy.init()
    node = VoiceAssistant("voice_assistant")
    try:
        node.speech_run()
    except KeyboardInterrupt:
        node.get_logger().info("用户中断程序")
    finally:
        node.asr.close()  # 释放麦克风资源
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()













# from openai import OpenAI
# import os
# import tempfile
# import asyncio
# from playsound import playsound
# import edge_tts
# import json
# import pyaudio
# from vosk import Model, KaldiRecognizer  
# import rclpy
# from rclpy.node import Node
# from expression_msgs.msg import ExpressionMsg
# import re
# from ament_index_python.packages import get_package_share_directory
# import pyaudio
# import dashscope,requests,wave
# from io import BytesIO
# api_key = "sk-52ef118f5c6d40ac9363b9aacd7829e8"
# base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
# model="qwen3-max"
# # model="qwen3-omni-flash"
# MODEL_PATH = os.path.join(get_package_share_directory('model_communication'),'resource',"vosk-model-small-cn-0.22")
# class My_client(OpenAI):
#     def __init__(self):
#         super().__init__(api_key=api_key,base_url=base_url)
#         #https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=2712576
#         self.model = model
#         # 设置输出数据的模态，当前支持两种：["text","audio"]、["text"]
#         self.modalities = ["text"]
#         # stream 必须设置为 True，否则会报错
#         self.stream = True
#         self.stream_options = {"include_usage": True}
#         self.max_tokens = 18
#         #top_p越高，生成的文本更多样。反之，生成的文本更确定。取值(0,1.0] float
#         self.top_p = 0.9
#         #temperature越高，生成的文本更多样，反之，生成的文本更确定。 取值(0,2] float
#         self.temperature = 1.9
#         # 生成过程中采样候选集的大小。例如，取值为50时，仅将单次生成中得分最高的50个Token组成随机采样的候选集。
#         # 取值越大，生成的随机性越高；取值越小，生成的确定性越高。 取值为None或当top_k大于100时，
#         # 表示不启用top_k策略，此时仅有top_p策略生效。取值需要大于或等于0。 (0,100)  int
#         self.top_k = 20
#         #是否开启思考 bool
#         self.enable_thinking =False
#         #最大思考长度 int
#         self.thinking_budget = 100



#         # 语音相关参数
#         self.audio_model = "qwen-tts"
#         self.voice = "Cherry"
#         self.language_type = "Chinese"  # 修复原代码的元组格式错误（去掉逗号）



#     def communication(self,input_msgs):
#         messages = [
#             {"role": "system", "content": "你是一个机器人，名叫小智,回答一定要简短，回复时一定要在句尾用()添加文字描述的表情，目前只能括号内只能有这几个文字描述:(开心,严肃,警觉,失落,正常,生气,心动),不要出现除了逗号句号括号以外的字符"},
#             {"role": "user", "content": input_msgs}
#         ]
#         return super().chat.completions.create(
#             model=self.model,
#             modalities=self.modalities,
#             stream=self.stream,
#             stream_options=self.stream_options,
#             messages=messages,
#             # max_tokens=self.max_tokens,
#             # top_p=self.top_p,
#             # temperature=self.temperature,
#             # enable_thinking = self.enable_thinking,

#             # top_k=self.top_k,
#             # temperature=self.temperature
#         )

# def get_message(completion):
#     output_msg = ''
#     for chunk in completion:
#         if chunk.choices:
#             content = chunk.choices[0].delta.content  # 获取content属性
#             output_msg += content

#         else:
#             print(f"Token使用:{chunk.usage.total_tokens}")
#     return output_msg


# class SaveWave:
#     def __init__(self, model_path):
       
        
#         self.model = Model(model_path)
        
#         self.rec = KaldiRecognizer(self.model, 16000)

        
#         self.p = pyaudio.PyAudio()
#         self.stream = self.p.open(
#             format=pyaudio.paInt16,  # 16位深度，vosk 要求的格式
#             channels=1,  # 单声道
#             rate=16000,  # 采样率，必须和识别器一致
#             input=True,  # 输入模式（麦克风）
#             frames_per_buffer=8192  # 缓冲区大小，不用改
#         )
#         self.stream.start_stream()

#     def listen(self):
#         print("正在监听...（说话后停顿一下，会自动识别）")
#         while True:
#             # 读取麦克风音频数据
#             data = self.stream.read(4096, exception_on_overflow=False)
#             # 没有音频数据时退出循环（比如麦克风被拔掉）
#             if len(data) == 0:
#                 print("未检测到音频输入")
#                 break
#             # 把音频数据传给识别器，当识别到完整句子时返回结果
#             if self.rec.AcceptWaveform(data):
#                 # 解析识别结果（JSON字符串转字典）
#                 result_dict = json.loads(self.rec.Result())
#                 # 提取识别到的文本
#                 text = result_dict.get("text", "").strip()
#                 if text:  # 有有效文本时返回
#                     return text
#         return None  # 没识别到有效内容时返回None

#     def close(self):
#         # 必须释放资源，否则麦克风会被占用
#         self.stream.stop_stream()
#         self.stream.close()
#         self.p.terminate()
#         print("资源已释放（麦克风关闭）")


# def play_audio_from_response(client, text):
#     """用完整文本生成并播放语音"""
#     try:
#         # 调用TTS生成完整音频
#         response = dashscope.MultiModalConversation.call(
#             model=client.audio_model,
#             api_key=api_key,
#             text=text,
#             voice=client.voice,
#             language_type=client.language_type
#         )
#         if response.status_code != 200:
#             return f"API调用失败：状态码{response.status_code}，信息{response.message}"

#         # 下载音频并播放
#         audio_url = response.output.audio.url
#         audio_data = requests.get(audio_url).content
#         with wave.open(BytesIO(audio_data), 'rb') as wav_file:
#             p = pyaudio.PyAudio()
#             stream = p.open(
#                 format=p.get_format_from_width(wav_file.getsampwidth()),
#                 channels=wav_file.getnchannels(),
#                 rate=wav_file.getframerate(),
#                 output=True
#             )
#             chunk = 1024
#             data = wav_file.readframes(chunk)
#             while data:
#                 stream.write(data)
#                 data = wav_file.readframes(chunk)
#             stream.stop_stream()
#             stream.close()
#             p.terminate()
#         return True
#     except Exception as e:
#         return f"播放失败：{str(e)}"

# def get_message2(client, full_text):
#     """先收集完整文本，再统一播放"""
#     # full_text = ""  # 存储完整回复文本
#     # for chunk in completion:
#     #     if chunk.choices and chunk.choices[0].delta.content:
#     #         # 累加文本片段，不立即播放
#     #         full_text += chunk.choices[0].delta.content
#     #     elif chunk.usage:
#     #         print(f"Token使用：{chunk.usage.total_tokens}")

#     # 所有文本收集完成后，一次性生成并播放语音
#     if full_text:
#         print(f"完整回复：{full_text}")
#         result = play_audio_from_response(client, full_text)
#         if result is not True:
#             print(result)
#     return full_text

# def text_to_speech(text):
#     async def _generate_audio(text, temp_filename):
#         communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoyiNeural")
#         await communicate.save(temp_filename)

#     with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
#         temp_filename = temp_file.name
#     try:

#         asyncio.run(_generate_audio(text, temp_filename))

#         playsound(temp_filename)
#     finally:
#         if os.path.exists(temp_filename):
#             os.remove(temp_filename)



# # if __name__ == '__main__':
# #     MODEL_PATH = "./vosk-model-small-cn-0.22"
# #     client = My_client()
# #     print("=== 通义千问-终端对话（输入 'exit' 退出）===")
# #     while True:
# #         print("(请说话)你:",end='')
# #         asr = SaveWave(MODEL_PATH)
# #         recognized_text = asr.listen()
# #         if recognized_text:
# #             print(recognized_text)
# #
# #             if not recognized_text.strip():
# #                 continue
# #
# #             response = get_message(client.communication(recognized_text))
# #             print(f"模型回复：{response}")
# #             text_to_speech(response)
# #
# #             if "退出" in recognized_text or "quit" in recognized_text or "exit" in recognized_text:
# #                 print("====对话结束====")
# #                 break


# class VoiceAssistant(Node):
#     def __init__(self,node_name):
#         super().__init__(node_name)  
#         self.client = My_client()
#         self.asr = SaveWave(MODEL_PATH)
#         self.get_logger().info("=== 语音助手 ===")
#         # self.subscriber_ = self.create_subscription(ExpressionMsg, "voice_text", self.callback, 10)
#         self.publisher_ = self.create_publisher(ExpressionMsg, "expressions", 10)
    
#     def speech_run(self):
#         while rclpy.ok():
#             msg = ExpressionMsg()

#             print("(请说话)你:",end='')
#             recognized_text = self.asr.listen()
#             print(recognized_text)
#             if "退出" in recognized_text or "quit" in recognized_text or "exit" in recognized_text:
#                 self.get_logger().info("=== 对话结束 ===")
                
#                 break

#             if not recognized_text.strip():
#                 continue
            
            
#             response = get_message(self.client.communication(recognized_text))
#             get_message2(self.client, response[:-4])

#             msg.stamp = self.get_clock().now().to_msg()
#             msg.expression = self.get_expression(response)

#             self.get_logger().info(f"模型回复：{response}")

#             self.publisher_.publish(msg)
            
#             # text_to_speech(response[:-4])
        


#     def run(self):
#         while rclpy.ok():
#             msg = ExpressionMsg()

#             user_input = input("你: ")
#             if "退出" in user_input or "quit" in user_input or "exit" in user_input:
#                 self.get_logger().info("=== 对话结束 ===")
                
#                 break

#             if not user_input.strip():
#                 continue
            
            
#             response = get_message(self.client.communication(user_input))

#             msg.stamp = self.get_clock().now().to_msg()
#             msg.expression = self.get_expression(response)

#             self.get_logger().info(f"模型回复：{response}")

#             self.publisher_.publish(msg)
#             text_to_speech(response[:-4])
#     def get_expression(self,res):
#         pattern = r"\((.*?)\)"
#         result = re.findall(pattern, res)
#         self.get_logger().info(f"result:{result[0]}")
#         return result[0] if result else "unknown"





# def main():
#     rclpy.init()
#     node = VoiceAssistant("voice_assistant")
#     try:
#         node.speech_run()  
#     except KeyboardInterrupt:
#         node.get_logger().info("用户中断程序")
#     finally:
#         node.destroy_node()  
#         rclpy.shutdown()     
    
    
