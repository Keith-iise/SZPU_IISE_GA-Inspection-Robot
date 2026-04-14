# # -- coding: utf-8 --
#
# import sys
# from ctypes import *
#
#
# from MvCameraControl_class import *
#
# HB_format_list = [
#     PixelType_Gvsp_HB_Mono8,
#     PixelType_Gvsp_HB_Mono10,
#     PixelType_Gvsp_HB_Mono10_Packed,
#     PixelType_Gvsp_HB_Mono12,
#     PixelType_Gvsp_HB_Mono12_Packed,
#     PixelType_Gvsp_HB_Mono16,
#     PixelType_Gvsp_HB_BayerGR8,
#     PixelType_Gvsp_HB_BayerRG8,
#     PixelType_Gvsp_HB_BayerGB8,
#     PixelType_Gvsp_HB_BayerBG8,
#     PixelType_Gvsp_HB_BayerRBGG8,
#     PixelType_Gvsp_HB_BayerGR10,
#     PixelType_Gvsp_HB_BayerRG10,
#     PixelType_Gvsp_HB_BayerGB10,
#     PixelType_Gvsp_HB_BayerBG10,
#     PixelType_Gvsp_HB_BayerGR12,
#     PixelType_Gvsp_HB_BayerRG12,
#     PixelType_Gvsp_HB_BayerGB12,
#     PixelType_Gvsp_HB_BayerBG12,
#     PixelType_Gvsp_HB_BayerGR10_Packed,
#     PixelType_Gvsp_HB_BayerRG10_Packed,
#     PixelType_Gvsp_HB_BayerGB10_Packed,
#     PixelType_Gvsp_HB_BayerBG10_Packed,
#     PixelType_Gvsp_HB_BayerGR12_Packed,
#     PixelType_Gvsp_HB_BayerRG12_Packed,
#     PixelType_Gvsp_HB_BayerGB12_Packed,
#     PixelType_Gvsp_HB_BayerBG12_Packed,
#     PixelType_Gvsp_HB_YUV422_Packed,
#     PixelType_Gvsp_HB_YUV422_YUYV_Packed,
#     PixelType_Gvsp_HB_RGB8_Packed,
#     PixelType_Gvsp_HB_BGR8_Packed,
#     PixelType_Gvsp_HB_RGBA8_Packed,
#     PixelType_Gvsp_HB_BGRA8_Packed,
#     PixelType_Gvsp_HB_RGB16_Packed,
#     PixelType_Gvsp_HB_BGR16_Packed,
#     PixelType_Gvsp_HB_RGBA16_Packed,
#     PixelType_Gvsp_HB_BGRA16_Packed]
#
# def save_non_raw_image(save_type, frame_info, cam_instance):
#
#     file_path = "Image_w%d_h%d_fn%d.png" % (
#         frame_info.stFrameInfo.nWidth, frame_info.stFrameInfo.nHeight, frame_info.stFrameInfo.nFrameNum)
#     mv_image_type = MV_Image_Png
#
#     c_file_path = file_path.encode('ascii')
#     stSaveParam = MV_SAVE_IMAGE_TO_FILE_PARAM_EX()
#     stSaveParam.enPixelType = frame_info.stFrameInfo.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
#     stSaveParam.nWidth = frame_info.stFrameInfo.nWidth  # ch:相机对应的宽 | en:Width
#     stSaveParam.nHeight = frame_info.stFrameInfo.nHeight  # ch:相机对应的高 | en:Height
#     stSaveParam.nDataLen = frame_info.stFrameInfo.nFrameLen
#     stSaveParam.pData = frame_info.pBufAddr
#     stSaveParam.enImageType = mv_image_type  # ch:需要保存的图像类型 | en:Image format to save
#     stSaveParam.pcImagePath = create_string_buffer(c_file_path)
#     stSaveParam.iMethodValue = 1
#     stSaveParam.nQuality = 80  # ch: JPG: (50,99], invalid in other format
#     mv_ret = cam_instance.MV_CC_SaveImageToFileEx(stSaveParam)
#     return mv_ret
#
#
# def save_raw(frame_info, cam_instance):
#     if frame_info.stFrameInfo.enPixelType in HB_format_list:
#
#         # ch:解码参数 | en: decode parameters
#         stDecodeParam = MV_CC_HB_DECODE_PARAM()
#         memset(byref(stDecodeParam), 0, sizeof(stDecodeParam))
#
#         # 获取数据包大小
#         stParam = MVCC_INTVALUE()
#         memset(byref(stParam), 0, sizeof(stParam))
#
#         ret = cam_instance.MV_CC_GetIntValue("PayloadSize", stParam)
#         if 0 != ret:
#             print("Get PayloadSize fail! ret[0x%x]" % ret)
#             return ret
#         nPayloadSize = stParam.nCurValue
#         stDecodeParam.pSrcBuf = frame_info.pBufAddr
#         stDecodeParam.nSrcLen = frame_info.stFrameInfo.nFrameLen
#         stDecodeParam.pDstBuf = (c_ubyte * nPayloadSize)()
#         stDecodeParam.nDstBufSize = nPayloadSize
#         ret = cam.MV_CC_HBDecode(stDecodeParam)
#         if ret != 0:
#             print("HB Decode fail! ret[0x%x]" % ret)
#             return ret
#         else:
#             file_path = "Image_w%d_h%d_fn%d.raw" % (stDecodeParam.nWidth, stDecodeParam.nHeight,
#                                                     stOutFrame.stFrameInfo.nFrameNum)
#             try:
#                 file_open = open(file_path.encode('ascii'), 'wb+')
#                 img_save = (c_ubyte * stDecodeParam.nDstBufLen)()
#                 memmove(byref(img_save), stDecodeParam.pDstBuf, stDecodeParam.nDstBufLen)
#                 file_open.write(img_save)
#             except PermissionError:
#                 file_open.close()
#                 print("save error raw file executed failed!")
#                 return MV_E_OPENFILE
#             file_open.close()
#     else:
#         file_path = "Image_w%d_h%d_fn%d.raw" % (
#             frame_info.stFrameInfo.nWidth, frame_info.stFrameInfo.nHeight, frame_info.stFrameInfo.nFrameNum)
#         try:
#             file_open = open(file_path.encode('ascii'), 'wb+')
#             img_save = (c_ubyte * frame_info.stFrameInfo.nFrameLen)()
#             memmove(byref(img_save), frame_info.pBufAddr, frame_info.stFrameInfo.nFrameLen)
#             file_open.write(img_save)
#         except PermissionError:
#             file_open.close()
#             print("save error raw file executed failed!")
#             return MV_E_OPENFILE
#         file_open.close()
#     return 0
#
#
# if __name__ == "__main__":
#
#     try:
#         # ch:初始化SDK | en: initialize SDK
#         MvCamera.MV_CC_Initialize()
#
#         deviceList = MV_CC_DEVICE_INFO_LIST()
#         tlayerType = (MV_GIGE_DEVICE | MV_USB_DEVICE | MV_GENTL_CAMERALINK_DEVICE
#                       | MV_GENTL_CXP_DEVICE | MV_GENTL_XOF_DEVICE)
#
#         # ch:枚举设备 | en:Enum device
#         ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
#         if ret != 0:
#             print("enum devices fail! ret[0x%x]" % ret)
#             sys.exit()
#
#         if deviceList.nDeviceNum == 0:
#             print("find no device!")
#             sys.exit()
#
#         print("Find %d devices!" % deviceList.nDeviceNum)
#
#         for i in range(0, deviceList.nDeviceNum):
#             mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
#             if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE or mvcc_dev_info.nTLayerType == MV_GENTL_GIGE_DEVICE:
#                 print("\ngige device: [%d]" % i)
#                 strModeName = ""
#                 for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
#                     if per == 0:
#                         break
#                     strModeName = strModeName + chr(per)
#                 print("device model name: %s" % strModeName)
#
#                 nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
#                 nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
#                 nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
#                 nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
#                 print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
#             elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
#                 print("\nu3v device: [%d]" % i)
#                 strModeName = ""
#                 for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
#                     if per == 0:
#                         break
#                     strModeName = strModeName + chr(per)
#                 print("device model name: %s" % strModeName)
#
#                 strSerialNumber = ""
#                 for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
#                     if per == 0:
#                         break
#                     strSerialNumber = strSerialNumber + chr(per)
#                 print("user serial number: %s" % strSerialNumber)
#             elif mvcc_dev_info.nTLayerType == MV_GENTL_CAMERALINK_DEVICE:
#                 print("\nCML device: [%d]" % i)
#                 strModeName = ""
#                 for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chModelName:
#                     if per == 0:
#                         break
#                     strModeName = strModeName + chr(per)
#                 print("device model name: %s" % strModeName)
#
#                 strSerialNumber = ""
#                 for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chSerialNumber:
#                     if per == 0:
#                         break
#                     strSerialNumber = strSerialNumber + chr(per)
#                 print("user serial number: %s" % strSerialNumber)
#             elif mvcc_dev_info.nTLayerType == MV_GENTL_CXP_DEVICE:
#                 print("\nCXP device: [%d]" % i)
#                 strModeName = ""
#                 for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chModelName:
#                     if per == 0:
#                         break
#                     strModeName = strModeName + chr(per)
#                 print("device model name: %s" % strModeName)
#
#                 strSerialNumber = ""
#                 for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chSerialNumber:
#                     if per == 0:
#                         break
#                     strSerialNumber = strSerialNumber + chr(per)
#                 print("user serial number: %s" % strSerialNumber)
#             elif mvcc_dev_info.nTLayerType == MV_GENTL_XOF_DEVICE:
#                 print("\nXoF device: [%d]" % i)
#                 strModeName = ""
#                 for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chModelName:
#                     if per == 0:
#                         break
#                     strModeName = strModeName + chr(per)
#                 print("device model name: %s" % strModeName)
#
#                 strSerialNumber = ""
#                 for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chSerialNumber:
#                     if per == 0:
#                         break
#                     strSerialNumber = strSerialNumber + chr(per)
#                 print("user serial number: %s" % strSerialNumber)
#
#         nConnectionNum = input("please input the number of the device to connect:")
#
#         if int(nConnectionNum) >= deviceList.nDeviceNum:
#             print("input error!")
#             sys.exit()
#
#         nSaveImageType = input("please input number (0-raw, 1-Jpeg, 2-Bmp, 3-Tiff, 4-Png):")
#         if int(nSaveImageType) not in {0, 1, 2, 3, 4}:
#             print("input error!")
#             sys.exit()
#
#         # ch:创建相机实例 | en:Create Camera Object
#         cam = MvCamera()
#
#         # ch:选择设备并创建句柄 | en:Select device and create handle
#         stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents
#
#         ret = cam.MV_CC_CreateHandle(stDeviceList)
#         if ret != 0:
#             raise Exception("create handle fail! ret[0x%x]" % ret)
#
#         # ch:打开设备 | en:Open device
#         ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
#         if ret != 0:
#             raise Exception("open device fail! ret[0x%x]" % ret)
#
#         # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
#         if stDeviceList.nTLayerType == MV_GIGE_DEVICE or stDeviceList.nTLayerType == MV_GENTL_GIGE_DEVICE:
#             nPacketSize = cam.MV_CC_GetOptimalPacketSize()
#             if int(nPacketSize) > 0:
#                 ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
#                 if ret != 0:
#                     print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
#             else:
#                 print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)
#
#         # ch:设置触发模式为off | en:Set trigger mode as off
#         ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
#         if ret != 0:
#             raise Exception("set trigger mode fail! ret[0x%x]" % ret)
#
#         # ch:开始取流 | en:Start grab image
#         ret = cam.MV_CC_StartGrabbing()
#         if ret != 0:
#             raise Exception("start grabbing fail! ret[0x%x]" % ret)
#
#         # ch:获取的帧信息 | en: frame from device
#         stOutFrame = MV_FRAME_OUT()
#         memset(byref(stOutFrame), 0, sizeof(stOutFrame))
#
#         ret = cam.MV_CC_GetImageBuffer(stOutFrame, 20000)
#         if None != stOutFrame.pBufAddr and 0 == ret:
#             print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
#             stOutFrame.stFrameInfo.nWidth, stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nFrameNum))
#
#             # ch:如果图像是HB格式，存raw需要先解码 | en:If save raw,and the image is HB format, should to be decoded first
#             if int(nSaveImageType) == 0:
#                 print(1)
#                 ret = save_raw(stOutFrame, cam)
#             else:
#                 print(2)
#                 ret = save_non_raw_image(int(nSaveImageType), stOutFrame, cam)
#             if ret != 0:
#                 cam.MV_CC_FreeImageBuffer(stOutFrame)
#                 raise Exception("save image fail! ret[0x%x]" % ret)
#             else:
#                 print("Save image success!")
#
#             cam.MV_CC_FreeImageBuffer(stOutFrame)
#         else:
#             raise Exception("no data[0x%x]" % ret)
#
#         # ch:停止取流 | en:Stop grab image
#         ret = cam.MV_CC_StopGrabbing()
#         if ret != 0:
#             raise Exception("stop grabbing fail! ret[0x%x]" % ret)
#
#         # ch:关闭设备 | Close device
#         ret = cam.MV_CC_CloseDevice()
#         if ret != 0:
#             raise Exception("close device fail! ret[0x%x]" % ret)
#
#         # ch:销毁句柄 | Destroy handle0
#         cam.MV_CC_DestroyHandle()
#
#     except Exception as e:
#         print(e)
#         cam.MV_CC_CloseDevice()
#         cam.MV_CC_DestroyHandle()
#     finally:
#         # ch:反初始化SDK | en: finalize SDK
#         MvCamera.MV_CC_Finalize()


# -- coding: utf-8 --

# import sys
import threading
# import os
import termios

# from ctypes import *
from MvCameraControl_class import *

g_bExit = False


# 为线程定义一个函数
def work_thread(cam=0, pData=0, nDataSize=0):
    stOutFrame = MV_FRAME_OUT()
    memset(byref(stOutFrame), 0, sizeof(stOutFrame))
    while True:
        ret = cam.MV_CC_GetImageBuffer(stOutFrame, 200)
        if ret == 0:
            print(
                "get one frame: Width[%d], Height[%d], PixelType[0x%x], nFrameNum[%d]" % (stOutFrame.stFrameInfo.nWidth,
                                                                                          stOutFrame.stFrameInfo.nHeight,
                                                                                          stOutFrame.stFrameInfo.enPixelType,
                                                                                          stOutFrame.stFrameInfo.nFrameNum))
            cam.MV_CC_FreeImageBuffer(stOutFrame)
        else:
            print("no data[0x%x]" % ret)
        if g_bExit == True:
            break


def press_any_key_exit():
    fd = sys.stdin.fileno()
    old_ttyinfo = termios.tcgetattr(fd)
    new_ttyinfo = old_ttyinfo[:]
    new_ttyinfo[3] &= ~termios.ICANON
    new_ttyinfo[3] &= ~termios.ECHO
    # sys.stdout.write(msg)
    # sys.stdout.flush()
    termios.tcsetattr(fd, termios.TCSANOW, new_ttyinfo)
    try:
        os.read(fd, 7)
    except:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_ttyinfo)


if __name__ == "__main__":

    # ch:初始化SDK | en: initialize SDK
    MvCamera.MV_CC_Initialize()

    SDKVersion = MvCamera.MV_CC_GetSDKVersion()
    print("SDKVersion[0x%x]" % SDKVersion)

    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = (
                MV_GIGE_DEVICE | MV_USB_DEVICE | MV_GENTL_CAMERALINK_DEVICE | MV_GENTL_CXP_DEVICE | MV_GENTL_XOF_DEVICE)

    # ch:枚举设备 | en:Enum device
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    if ret != 0:
        print("enum devices fail! ret[0x%x]" % ret)
        sys.exit()

    if deviceList.nDeviceNum == 0:
        print("find no device!")
        sys.exit()

    print("Find %d devices!" % deviceList.nDeviceNum)

    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE or mvcc_dev_info.nTLayerType == MV_GENTL_GIGE_DEVICE:
            print("\ngige device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)

            nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            print("\nu3v device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print("user serial number: %s" % strSerialNumber)
        elif mvcc_dev_info.nTLayerType == MV_GENTL_CAMERALINK_DEVICE:
            print("\nCML device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print("user serial number: %s" % strSerialNumber)
        elif mvcc_dev_info.nTLayerType == MV_GENTL_XOF_DEVICE:
            print("\nXoF device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print("user serial number: %s" % strSerialNumber)
        elif mvcc_dev_info.nTLayerType == MV_GENTL_CXP_DEVICE:
            print("\nCXP device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print("user serial number: %s" % strSerialNumber)

    if sys.version >= '3':
        nConnectionNum = input("please input the number of the device to connect:")
    else:
        nConnectionNum = input("please input the number of the device to connect:")

    if int(nConnectionNum) >= deviceList.nDeviceNum:
        print("intput error!")
        sys.exit()

    # ch:创建相机实例 | en:Creat Camera Object
    cam = MvCamera()

    # ch:选择设备并创建句柄| en:Select device and create handle
    stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print("create handle fail! ret[0x%x]" % ret)
        sys.exit()
    print(stDeviceList)

    # ch:打开设备 | en:Open device
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print("open device fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
    if stDeviceList.nTLayerType == MV_GIGE_DEVICE or stDeviceList.nTLayerType == MV_GENTL_GIGE_DEVICE:
        nPacketSize = cam.MV_CC_GetOptimalPacketSize()
        if int(nPacketSize) > 0:
            ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
            if ret != 0:
                print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
        else:
            print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

    # ch:设置触发模式为off | en:Set trigger mode as off
    ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
    if ret != 0:
        print("set trigger mode fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:获取数据包大小 | en:Get payload size
    stParam = MVCC_INTVALUE()
    memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))

    ret = cam.MV_CC_GetIntValue("PayloadSize", stParam)
    if ret != 0:
        print("get payload size fail! ret[0x%x]" % ret)
        sys.exit()
    nPayloadSize = stParam.nCurValue

    # ch:开始取流 | en:Start grab image
    ret = cam.MV_CC_StartGrabbing()
    if ret != 0:
        print("start grabbing fail! ret[0x%x]" % ret)
        sys.exit()

    data_buf = (c_ubyte * nPayloadSize)()

    try:
        hThreadHandle = threading.Thread(target=work_thread, args=(cam, byref(data_buf), nPayloadSize))
        hThreadHandle.start()
    except:
        print("error: unable to start thread")

    print("press a key to stop grabbing.")
    press_any_key_exit()

    g_bExit = True
    hThreadHandle.join()

    # ch:停止取流 | en:Stop grab image
    ret = cam.MV_CC_StopGrabbing()
    if ret != 0:
        print("stop grabbing fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    # ch:关闭设备 | Close device
    ret = cam.MV_CC_CloseDevice()
    if ret != 0:
        print("close deivce fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    # ch:销毁句柄 | Destroy handle
    ret = cam.MV_CC_DestroyHandle()
    if ret != 0:
        print("destroy handle fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    del data_buf

    # ch:反初始化SDK | en: finalize SDK
    MvCamera.MV_CC_Finalize()