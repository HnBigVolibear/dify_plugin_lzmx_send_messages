from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import requests
import json
import urllib3
import base64
import random

urllib3.disable_warnings()

class tool_lzmx_send_img(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        net_mode = None
        try:
            net_mode = tool_parameters.get("is_www_to_lzmx", "DCN") == '公网'
            print('**当前网络模式是否为公网: ', net_mode)
        except KeyError:
            raise Exception("is_www_to_lzmx 未配置或无效。请在插件授权设置中选择您的网络模式！")
        
        # 弃用，不再解析图片的尺寸！为了兼容性。。。不敢再依赖Pillow库了。。。
        # is_have_Pillow = False
        # try:
        #     from PIL import Image
        #     print("Pillow 库已安装，可以正常使用 Image 模块。")
        #     is_have_Pillow = True
        # except ImportError:
        #     print("错误：未找到 Pillow 库, 本次不再读取图片宽高。")
        
        lzmx_key = tool_parameters.get("robot_key", "")
        send_img_files = tool_parameters.get("send_img_files", None)
        send_img_base64 = tool_parameters.get("send_img_base64", "")

        img_width = tool_parameters.get("img_width", 0)
        img_height = tool_parameters.get("img_height", 0)
        if img_width is None or img_width=='':
            img_width = 0
        if img_height is None or img_height=='':
            img_height = 0
        
        webhook_url = ""
        upload_url = ""
        headers = {'Content-Type': 'application/json'}

        if (send_img_base64 is None or len(send_img_base64)<32) and (send_img_files is None or len(send_img_files) == 0) :
            raise Exception("执行失败! 请至少选择一张图片文件、或输入一个图片的Base64编码! ")
        
        # 一、首先尝试发送send_img_files
        if send_img_files is not None and len(send_img_files) > 0:
            fileId = None
            file_name = ''
            # 支持多选！因此这里直接循环遍历，挨个发送图片！
            is_all_suc = True
            is_all_Fail = True
            for send_img_file in send_img_files:
                content = None
                try:
                    # 至关重要的读取内容的命令！
                    # 这一行报错，则说明当前Dify平台的.env全局配置文件里，未设置FILES_URL，导致不同容器间无法共享文件流，该情况会导致灾难性后果，几乎所有文件读写类的第三方插件都会随之失效崩溃，Dify平台管理员请务必注意此项配置要无误！
                    content = send_img_file.blob
                    
                    print('files.blob读取内容流 -> 成功! ')
                except Exception as e:
                    raise Exception("【严重错误】files.blob读取内容流 -> 直接失败！说明当前Dify平台根本不支持后台读取文件流！因此本插件完全无法正常运行！\n可能原因是：\n当前Dify平台的.env全局配置文件里，未设置FILES_URL，导致不同容器间无法共享文件流，该情况会导致灾难性后果，几乎所有文件读写类的第三方插件都会随之失效，并不只是影响本插件了。Dify平台管理员请务必注意此项配置要无误！\n解决办法：\n在.env全局配置文件里，设置：FILES_URL=http://dify服务器的内网IP\n")  
                
                fileId = None
                file_name = '初始名字为空.png'
                try:
                    file_name = send_img_file.filename
                    print(f'成功解析到当前的图片名：{file_name}')
                except Exception as e:
                    random_number = str(random.randint(10**9, 10**10 - 1)) # 生成随机名字
                    file_name = f'random_file_{random_number}.png'
                    yield self.create_text_message(f"当前图片尝试获取文件名失败！自动生成随机名字: \n{file_name}")
                
                try:
                    file_type = '*/*'
                    files = {
                        'file': (file_name, content, file_type)
                    }

                    response = None
                    if net_mode:
                        # print('当前通过公网发送量子密信')
                        upload_url = f"https://imtwo.zdxlz.com/im-external/v1/webhook/upload-attachment?key={lzmx_key}&type=1"
                        response = requests.post(upload_url, files=files, timeout=4)
                    else:
                        # print('当前通过DCN发送量子密信')
                        upload_url = f"https://134.64.75.9:1443/im-external/v1/webhook/upload-attachment?key={lzmx_key}&type=1"
                        response = requests.post(upload_url, files=files, verify=False, timeout=4)

                    if response.json().get('code') == 200:
                        print(response.json())
                        fileId = response.json().get('data').get('id')
                        yield self.create_text_message(f"图片{file_name}上传成功，上传fileId: \n{fileId}\n")
                    else:
                        yield self.create_text_message(f"图片{file_name}上传失败。接口返回错误信息: \n{response.json()}\n")
                        is_all_suc = False
                        continue # 直接尝试下一张图片
                except Exception as e:
                    yield self.create_text_message(f'图片{file_name}上传失败。失败报错如下：\n{str(e)}\n')
                    is_all_suc = False
                    continue # 直接尝试下一张图片

                if fileId == None:
                    yield self.create_text_message(f'图片{file_name}上传失败。fileId返回为空。\n')
                    is_all_suc = False
                    continue # 直接尝试下一张图片

                data = None
                img_width_send = 1296 # 量子密信默认的图片发送宽度
                img_height_send = 455 # 量子密信默认的图片发送高度
                if img_height==0 or img_width==0:
                    # print('本次不指定图片宽高！')
                    # if is_have_Pillow:
                    #     try:
                    #         image = Image.open(io.BytesIO(content))
                    #         img_width_send, img_height_send = image.size
                    #         print(f'成功读取到宽高：{img_width_send} {img_height_send}')
                    #     except Exception as e:
                    #         print(f"获取图片尺寸出错：{str(e)}")
                    print('本次不指定图片宽高! 直接用量子密信默认的宽高。')
                else:
                    print('本次指定图片宽高！')
                    img_width_send = img_width+0
                    img_height_send = img_height+0
                # 现在统一设置图片最终发送的宽高：
                data = {
                    'type': 'image',
                    'imageMsg': {
                        'fileId': fileId,
                        "height": img_height_send,
                        "width": img_width_send
                    }
                }
                
                try:
                    response = None
                    if net_mode:
                        # print('当前通过公网发送量子密信')
                        webhook_url = f"http://imtwo.zdxlz.com/im-external/v1/webhook/send?key={lzmx_key}" 
                        response = requests.post(webhook_url, data=json.dumps(data), headers=headers, timeout=4)
                    else:
                        # print('当前通过DCN发送量子密信')
                        webhook_url = f"https://134.64.75.9:1443/im-external/v1/webhook/send?key={lzmx_key}" 
                        response = requests.post(webhook_url, data=json.dumps(data), headers=headers, verify=False, timeout=4)
                    print('最终的发送接口返回：', response.json())
                    if response.json().get('code') == 200:
                        yield self.create_text_message(f'图片{file_name}发送成功！\n')
                        is_all_Fail = False
                    else:
                        yield self.create_text_message(f"图片{file_name}发送失败(但第一步上传是成功的)。接口返回错误信息: \n{response.json()}\n")
                        is_all_suc = False
                        continue # 直接尝试下一张图片
                except Exception as e:
                    yield self.create_text_message(f'图片{file_name}发送失败(但第一步上传是成功的)。失败报错如下：\n{str(e)}\n')
                    is_all_suc = False
                    continue # 直接尝试下一张图片
            if is_all_suc:
                yield self.create_text_message(f'全部图片发送成功！\n')
            else:
                yield self.create_text_message(f'存在发送失败的图片，请检查！\n')
            if is_all_Fail:
                raise Exception('全部图片均发送失败! 请联系平台管理员!')

        # 二、然后尝试发送send_img_base64 
        # 正确的编码应该是类似于："data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...AAAABJRU5ErkJggg=="
        if send_img_base64 is not None and len(send_img_base64)>32:
            fileId = None
            response = None
            try:
                # 分割 Data URL
                header, encoded_data = send_img_base64.split(",", 1)
                # 提取 MIME 类型
                file_type = header.split(";")[0].split(":")[1]
                print(f"MIME 类型: {file_type}")  # 输出: image/png
                # 解码 Base64 数据
                content = base64.b64decode(encoded_data)
                random_number = str(random.randint(10**9, 10**10 - 1)) # 生成随机名字
                files = {
                    'file': (f'image_{random_number}.' + file_type.split('/')[1], content, file_type)  # 文件名、二进制数据、MIME 类型
                }

                if net_mode:
                    # print('当前通过公网发送量子密信')
                    upload_url = f"https://imtwo.zdxlz.com/im-external/v1/webhook/upload-attachment?key={lzmx_key}&type=1"
                    response = requests.post(upload_url, files=files, timeout=4)
                else:
                    # print('当前通过DCN发送量子密信')
                    upload_url = f"https://134.64.75.9:1443/im-external/v1/webhook/upload-attachment?key={lzmx_key}&type=1"
                    response = requests.post(upload_url, files=files, verify=False, timeout=4)

                if response.json().get('code') == 200:
                    print(response.json())
                    fileId = response.json().get('data').get('id')
                    yield self.create_text_message(f"base64图片上传成功，上传fileId: \n{fileId}\n")
                else:
                    yield self.create_text_message(f"base64图片上传失败。接口返回错误信息: \n{response.json()}\n")
            except Exception as e:
                yield self.create_text_message(f'base64图片上传失败。失败报错如下：\n{str(e)}\n')

            if fileId == None:
                yield self.create_text_message(f'base64图片上传失败。fileId返回为空。\n')
            else:
                data = None
                img_width_send = 1296 # 量子密信默认的图片发送宽度
                img_height_send = 455 # 量子密信默认的图片发送高度
                if img_height==0 or img_width==0:
                    # print('本次不指定图片宽高！')
                    # if is_have_Pillow:
                    #     try:
                    #         image = Image.open(io.BytesIO(content))
                    #         img_width_send, img_height_send = image.size
                    #         print(f'成功读取到宽高：{img_width_send} {img_height_send}')
                    #     except Exception as e:
                    #         print(f"获取图片尺寸出错：{str(e)}")
                    print('本次不指定图片宽高! 直接用量子密信默认的宽高。')
                else:
                    print('本次指定图片宽高！')
                    img_width_send = img_width+0
                    img_height_send = img_height+0
                # 现在统一设置图片最终发送的宽高：
                data = {
                    'type': 'image',
                    'imageMsg': {
                        'fileId': fileId,
                        "height": img_height_send,
                        "width": img_width_send
                    }
                }
                
                try:
                    response = None
                    if net_mode:
                        # print('当前通过公网发送量子密信')
                        webhook_url = f"http://imtwo.zdxlz.com/im-external/v1/webhook/send?key={lzmx_key}" 
                        response = requests.post(webhook_url, data=json.dumps(data), headers=headers, timeout=4)
                    else:
                        # print('当前通过DCN发送量子密信')
                        webhook_url = f"https://134.64.75.9:1443/im-external/v1/webhook/send?key={lzmx_key}" 
                        response = requests.post(webhook_url, data=json.dumps(data), headers=headers, verify=False, timeout=4)
                    print('最终的发送接口返回：', response.json())
                    if response.json().get('code') == 200:
                        yield self.create_text_message(f'base64图片发送成功!\n')
                    else:
                        yield self.create_text_message(f"base64图片发送失败(但第一步上传是成功的)。接口返回错误信息: \n{response.json()}\n")
                except Exception as e:
                    yield self.create_text_message(f'base64图片发送失败(但第一步上传是成功的)。失败报错如下：\n{str(e)}\n')
               