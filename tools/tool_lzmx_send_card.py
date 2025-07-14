from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import requests
import json
import urllib3

urllib3.disable_warnings()

class tool_lzmx_send_card(Tool):
    # _invoke方法，最关键的方法，用户在页面里使用本工具时，就是触发这个方法！
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        net_mode = None
        try:
            net_mode = tool_parameters.get("is_www_to_lzmx", "DCN") == '公网'
            print('**当前网络模式是否为公网: ', net_mode)
        except KeyError:
            raise Exception("is_www_to_lzmx 未配置或无效。请在插件授权设置中选择您的网络模式！")
        
        # 1、首先读取本工具的入参。
        lzmx_key = tool_parameters.get("robot_key", "")
        if len(lzmx_key) < 6:
            raise Exception('请输入正确的量子密信群机器人的密钥key !')
        
        card_title = tool_parameters.get("card_title", "")
        card_description = tool_parameters.get("card_description", "")
        card_url = tool_parameters.get("card_url", "")
        card_pic_url = tool_parameters.get("card_pic_url", "")

        if len(card_title)==0 or len(card_description)==0:
            raise Exception('图文卡片的标题或描述正文，不能为空！')
        
        # 还需要对推送内容进行一些整理！比如，量子密信不允许推送跨域的网址！
        card_title = card_title.replace('http://','h t t p ：/ / ').replace('https://','h t t p s ：/ / ').replace('\n\n\n','\n\n')
        card_title = card_title.strip()
        card_description = card_description.replace('http://','h t t p ：/ / ').replace('https://','h t t p s ：/ / ').replace('\n\n\n','\n\n')
        card_description = card_description.strip()
        
        
        # 2、现在开始处理真正的业务功能逻辑
        # （1）先生成请求体
        headers = {'Content-Type': 'application/json'}
        data = {
            'type': 'news',
            'news': {
                'info': {
                    'title': card_title,
                    'description': card_description,
                    'url':card_url,
                    'picUrl':card_pic_url,
                }
            }
        }
        # （2）实际发起请求
        try:
            response = None
            if net_mode:
                # print('当前通过公网发送量子密信')
                webhook_url = f"http://imtwo.zdxlz.com/im-external/v1/webhook/send?key={lzmx_key}" 
                response = requests.post(webhook_url, data=json.dumps(data), headers=headers, timeout=4)
            else:
                # print('当前通过DCN发送量子密信。考虑信息安全，下面这里的办公内网IP不予公开！')
                webhook_url = f"https://XXX.XXX.XXX.XXX:XXXX/im-external/v1/webhook/send?key={lzmx_key}" 
                response = requests.post(webhook_url, data=json.dumps(data), headers=headers, verify=False, timeout=4)
            # 3、返回执行结果
            if response.json().get('code') == 200:
                yield self.create_text_message('图文卡片发送成功')
            else:
                print("发送失败。接口返回的错误信息: ", response.json().get('message'))
                raise Exception(f"图文卡片发送失败。接口返回的错误信息: \n{str(response.json().get('message'))}")
                # 这里依旧raise抛出异常，而不选择yield返回，是为了配合Dify插件自带的“重试”开关的功能！
        except Exception as e:
            raise Exception(f'图文卡片发送失败。本次接口发起就直接失败，报错如下：\n{str(e)}')
