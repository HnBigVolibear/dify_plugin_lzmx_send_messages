from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import requests
import json
import urllib3
import random
import os

urllib3.disable_warnings()

class tool_lzmx_send_file(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        net_mode = None
        try:
            net_mode = tool_parameters.get("is_www_to_lzmx", "DCN") == '公网'
            print('**当前网络模式是否为公网: ', net_mode)
        except KeyError:
            raise Exception("is_www_to_lzmx 未配置或无效。请在插件授权设置中选择您的网络模式！")
        
        lzmx_key = tool_parameters.get("robot_key", "")
        send_files = tool_parameters.get("send_files", "")
        
        headers = {'Content-Type': 'application/json'}
        if send_files is not None and len(send_files) > 0:
            fileId = None
            file_name = ''
            # 支持多选！因此这里直接循环遍历，挨个发送文件！
            is_all_suc = True
            is_all_Fail = True
            file_index = 0
            for send_file in send_files:
                content = None
                try:
                    # 至关重要的读取内容的命令！
                    # 这一行报错，则说明当前Dify平台的.env全局配置文件里，未设置FILES_URL，导致不同容器间无法共享文件流，该情况会导致灾难性后果，几乎所有文件读写类的第三方插件都会随之失效崩溃，Dify平台管理员请务必注意此项配置要无误！
                    content = send_file.blob
                    
                    print('files.blob读取内容流 -> 成功! ')
                except Exception as e:
                    raise Exception("【严重错误】files.blob读取内容流 -> 直接失败！说明当前Dify平台根本不支持后台读取文件流！因此本插件完全无法正常运行！\n可能原因是：\n当前Dify平台的.env全局配置文件里，未设置FILES_URL，导致不同容器间无法共享文件流，该情况会导致灾难性后果，几乎所有文件读写类的第三方插件都会随之失效，并不只是影响本插件了。Dify平台管理员请务必注意此项配置要无误！\n解决办法：\n在.env全局配置文件里，设置：FILES_URL=http://dify服务器的内网IP\n")  
                
                fileId = None
                file_name = tool_parameters.get("rename", "").strip()
                if file_name is None or len(file_name)<3:
                    try:
                        file_name = send_file.filename
                        print(f'成功解析到当前的文件名：{file_name}')
                    except Exception as e:
                        random_number = str(random.randint(10**9, 10**10 - 1)) # 生成随机名字
                        file_name = f'random_file_{random_number}.bak'
                        yield self.create_text_message(f"当前文件尝试获取文件名失败！自动生成随机名字: \n{file_name}")
                else:
                    if "." not in file_name:
                        raise Exception("对不起，你提供的重命名新文件名，未包含后缀名，不是一个完整的文件名！正确例子比如是：xxx.doc")
                    file_index = file_index + 1
                    if file_index > 1: # 从第二个文件开始，自动增加序号名字！
                        fname, ext = os.path.splitext(file_name)
                        file_name = f"{fname}_{str(file_index)}{ext}"
                try:
                    file_type = '*/*'
                    files = {
                        'file': (file_name, content, file_type)
                    }
                    response = None
                    if net_mode:
                        # print('当前通过公网发送量子密信')
                        upload_url = f"https://imtwo.zdxlz.com/im-external/v1/webhook/upload-attachment?key={lzmx_key}&type=2"
                        response = requests.post(upload_url, files=files, timeout=4)
                    else:
                        # print('当前通过DCN发送量子密信')
                        upload_url = f"https://134.64.75.9:1443/im-external/v1/webhook/upload-attachment?key={lzmx_key}&type=2"
                        response = requests.post(upload_url, files=files, verify=False, timeout=4)

                    if response.json().get('code') == 200:
                        print(response.json())
                        fileId = response.json().get('data').get('id')
                        yield self.create_text_message(f"文件{file_name}上传成功，上传fileId: \n{fileId}\n")
                    else:
                        yield self.create_text_message(f"文件{file_name}上传失败。接口返回错误信息: \n{response.json()}\n")
                        is_all_suc = False
                        continue # 直接尝试下一个文件
                except Exception as e:
                    yield self.create_text_message(f'文件{file_name}上传失败。失败报错如下：\n{str(e)}\n')
                    is_all_suc = False
                    continue # 直接尝试下一个文件

                if fileId == None:
                    yield self.create_text_message(f'文件{file_name}上传失败。fileId返回为空。\n')
                    is_all_suc = False
                    continue # 直接尝试下一个文件

                data = {
                    'type': 'file',
                    'fileMsg': {
                        'fileId': fileId
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
                        yield self.create_text_message(f'文件{file_name}发送成功！\n')
                        is_all_Fail = False
                    else:
                        yield self.create_text_message(f"文件{file_name}发送失败(但第一步上传是成功的)。接口返回错误信息: \n{response.json()}\n")
                        is_all_suc = False
                        continue # 直接尝试下一个文件
                except Exception as e:
                    yield self.create_text_message(f'文件{file_name}发送失败(但第一步上传是成功的)。失败报错如下：\n{str(e)}\n')
                    is_all_suc = False
                    continue # 直接尝试下一个文件
            if is_all_suc:
                yield self.create_text_message('全部文件发送成功！\n')
            else:
                yield self.create_text_message('存在发送失败的文件，请检查！\n')
            if is_all_Fail:
                raise Exception('全部文件均发送失败! 请联系平台管理员!')
        else:
            raise Exception('执行失败！请至少选择一个文件！')