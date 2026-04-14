
import sys
import threading
# import os
import termios

# from ctypes import *
import cv2
import numpy as np

if __name__ == '__main__':
    from MvCameraControl_class import *
    from CameraParams_header import *
else:
    from Camera.MvCameraControl_class import *
    from Camera.CameraParams_header import *

class Camera:
    def __init__(self,camera_index):
        # 初始化SDK
        MvCamera.MV_CC_Initialize()

        # 获取设别列表
        self._deviceList = MV_CC_DEVICE_INFO_LIST()

        # 设置设备类型
        self._tlayerType = MV_USB_DEVICE

        # 相机参数
        self._stParam = None

        # 数据包大小
        self._nPayloadSize = None

        # 数据流
        self._data_buf = None

        # 相机索引存储
        self._camera_index = camera_index

        # 设备信息打印
        self._Show_info = True

        # 枚举设备
        MvCamera.MV_CC_EnumDevices(self._tlayerType, self._deviceList)

        # 获取SDK版本号
        self.SDKVersion = MvCamera.MV_CC_GetSDKVersion()

        if self._Show_info:
            self._print_info()


        self._open()


    def _print_info(self):
        print("SDK版本[0x%x]" % self.SDKVersion)
        print("发现 %d 个设备!" % self._deviceList.nDeviceNum)
        for i in range(0, self._deviceList.nDeviceNum):
            mvcc_dev_info = cast(self._deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nu3v 设备号: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("设备名称: [%s]" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("串行代号: %s" % strSerialNumber)


    def _open(self):
        if int(self._camera_index) >= self._deviceList.nDeviceNum:
            print("设备索引错误！")
            sys.exit()

        # 创建相机实例
        self._cam = MvCamera()

        # 选择设备并创建句柄
        _stDeviceList = cast(self._deviceList.pDeviceInfo[int(self._camera_index)], POINTER(MV_CC_DEVICE_INFO)).contents

        ret = self._cam.MV_CC_CreateHandle(_stDeviceList)
        if ret != 0:
            print("创建句柄失败! ret[0x%x]" % ret)
            sys.exit()

        # 打开设备
        ret = self._cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print("打开设备失败! ret[0x%x]" % ret)
            sys.exit()

        # 设置触发模式为off
        ret = self._cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            print("触发模式设置失败! ret[0x%x]" % ret)
            sys.exit()

        # 获取数据包大小
        self._stParam = MVCC_INTVALUE()
        memset(byref(self._stParam), 0, sizeof(MVCC_INTVALUE))

        ret = self._cam.MV_CC_GetIntValue("PayloadSize", self._stParam)
        if ret != 0:
            print("获取载荷失败! ret[0x%x]" % ret)
            sys.exit()
        self._nPayloadSize = self._stParam.nCurValue

        # 开始取流
        ret = self._cam.MV_CC_StartGrabbing()
        if ret != 0:
            print("开始取流失败! ret[0x%x]" % ret)
            sys.exit()

        self._data_buf = (c_ubyte * self._nPayloadSize)()


    def release(self):
        # ch:停止取流 | en:Stop grab image
        ret = self._cam.MV_CC_StopGrabbing()
        if ret != 0:
            print("停止取流失败! ret[0x%x]" % ret)
            del self._data_buf
            sys.exit()

        # ch:关闭设备 | Close device
        ret = self._cam.MV_CC_CloseDevice()
        if ret != 0:
            print("关闭设备失败l! ret[0x%x]" % ret)
            del self._data_buf
            sys.exit()

        # ch:销毁句柄 | Destroy handle
        ret = self._cam.MV_CC_DestroyHandle()
        if ret != 0:
            print("句柄销毁失败! ret[0x%x]" % ret)
            del self._data_buf
            sys.exit()

        del self._data_buf

        # ch:反初始化SDK | en: finalize SDK
        MvCamera.MV_CC_Finalize()

    def read(self):
        ret_flag = False
        image = None
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))

        # 获取图像缓冲区
        ret = self._cam.MV_CC_GetImageBuffer(stOutFrame, 100)
        if ret != 0:
            print(f"GetImageBuffer failed! Error code: 0x{ret:x}")
            return ret_flag, None

        try:
            ret_flag = True
            frame_info = stOutFrame.stFrameInfo

            # 获取实际图像尺寸（考虑扩展尺寸）
            width = frame_info.nExtendWidth if frame_info.nExtendWidth > 0 else frame_info.nWidth
            height = frame_info.nExtendHeight if frame_info.nExtendHeight > 0 else frame_info.nHeight
            pixel_type = frame_info.enPixelType
            data_size = frame_info.nFrameLen

            # 创建图像数据缓冲区
            img_buff = (c_ubyte * data_size).from_address(addressof(stOutFrame.pBufAddr.contents))


            bayer_image = np.frombuffer(img_buff, dtype=np.uint8).reshape(height, width)
            image = cv2.cvtColor(bayer_image, cv2.COLOR_BayerRG2RGB)



        except Exception as e:
            print(f"图像获取进程错误: {str(e)}")
            ret_flag = False
        finally:
            # 释放图像缓冲区
            ret_free = self._cam.MV_CC_FreeImageBuffer(stOutFrame)
            if ret_free != 0:
                print(f"释放图像缓冲失败 ret: 0x{ret_free:x}")

        return ret_flag, image



def camera_example():
    import time
    camera = Camera(0)

    prev_frame_time = 0
    new_frame_time = 0
    while True:
        ret,img = camera.read()
        if not ret:
            continue
        resize_frame = cv2.resize(img, (640, 480))
        # 计算当前帧的帧率
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time

        # 将fps转换为整数以便显示
        fps = int(fps)

        # 在帧上显示帧率
        cv2.putText(resize_frame, str(fps), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow('Camera 1', resize_frame)
        if cv2.waitKey(1) & 0xff == 27:
            camera.close()
            break
def main():
    camera_example()


if __name__ == '__main__':
    main()
