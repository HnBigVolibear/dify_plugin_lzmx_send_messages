from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class LzmxSendMessageProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            """
            IMPLEMENT YOUR VALIDATION HERE

            中国电信量子密信消息推送器, 支持推送4种消息: 文本、图片、文件、图文卡片。
            支持公网和DCN网。
            湖南电信省云调倾情出品! 
            特别说明: 
                如果需要推送图片与文件, 需Dify平台.env全局配置文件里修改设置FILES_URL参数为服务器IP地址, 否则本插件无法生效 !!!
            """
            # # 读取工具整体入参授权的示例：
            # tools_param = credentials['is_www_to_lzmx']
            # print('当前网络模式选择为：', str(tools_param))
            pass
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
