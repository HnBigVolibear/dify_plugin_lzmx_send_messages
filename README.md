## lzmx_send_message      
### 自制Dify插件：量子密信消息推送器 

![img](./_assets/lzmx.png)

**Author:** HnBigVolibear 湖南大白熊

**Version:** 0.4.6

**Type:** tool

**UpdateTime:** 2025-07-12 15:31:26

## 自己的工具自己造

### 工具介绍
量子密信消息推送器，支持推送全部4种消息：文本、图片、文件、卡片；
且支持公网和DCN网！

#### 使用须知：
（1）考虑信息安全，脚本里面的办公内网IP不予公开！但是你仍然可以直接下载发行版插件安装包正常使用本插件。
（2）若选择通过办公内网推送消息，则需要您的服务器IP被量子密信官方侧放通IP白名单，请自行联系申请！（公网无限制）

#### （一）文本推送
##### 入参：
1、量子密信群机器人的key - string格式，必填。

2、发送内容 - string格式，必填。

3、艾特人员列表 - string格式，可选。填入要艾特群成员的手机号即可。支持艾特多个人：以逗号、分号、竖杠隔开多个人的手机号码即可；同时，支持艾特所有人，直接填“所有人”即可。

4、发送消息使用的网络类型 - 字典值，必填，仅限“公网”或“DCN”，默认初始是“DCN”！

##### 出参：
本次发送是否成功 - string格式。

注：部分失败情况，会返回失败报错原因。

##### 【特别说明】
由于量子密信的消息保护机制，大部分http链接网址形式的字符串，都会被屏蔽，从而导致发送失败！因此，本插件为了保险，统一将网址的http、https进行了空格插值，类似于“h t t p:/ /”这样的机制。

#### （二）图片推送
##### 入参：
1、量子密信群机器人的key - string格式，必填。

2、发送图片的文件流 - Array[file]格式，可选。支持发送多张图片。

3、发送图片的Base64编码 - string格式，可选。形如：'data:image/png;base64,......'

4、图片密信内展示宽度px - Number格式，可选。为空或填0，则不生效。

5、图片密信内展示高度px - Number格式，可选。为空或填0，则不生效。

6、发送消息使用的网络类型 - 字典值，必填，仅限“公网”或“DCN”，默认初始是“DCN”！

注：2种图片形式，必须至少1种图片选择不为空！即至少要发送一张图片！

##### 出参：
本次发送是否成功 - string格式。

注：多张图片时，会返回每张图片是否发生成功。

##### 【特别说明】
**宽高设置为空或为0时的默认发送图片原始尺寸的设计，当前版本已弃用！**

原因是：此设计涉及image图像读取处理，因此需要本插件依赖Python的第三方库Pillow，本来正常情况是可以支持的。但是由于Dify需增加安装的依赖库，可能会导致一些本地部署的Dify平台在导入本插件时失败、报错、无法生效等各种意想不到的问题Bug，因此为了追求稳定性，只能忍痛割爱！

#### （三）文件推送
##### 入参：
1、量子密信群机器人的key - string格式，必填。

2、发送文件流 - Array[file]格式，必填。支持发送多个文件。

3、发送消息使用的网络类型 - 字典值，必填，仅限“公网”或“DCN”，默认初始是“DCN”！

4、重命名 - string格式，可选（V0.4.3新特性！）。一般不填, 即默认文件原名。请注意，这里你需要写完整名称，即带上后缀，比如“xxx.doc”。批量发送多文件时将自动后缀+1！

##### 出参：
本次发送是否成功 - string格式。

注：多个文件时，会返回每个文件是否发生成功。

#### （四）图文卡片推送
##### 入参：
1、量子密信群机器人的key - string格式，必填。

2、卡片标题 - string格式，必填。

3、卡片正文描述 - string格式，必填。

4、卡片点击跳转链接 - string格式，必填。

5、卡片背景图的链接 - string格式，必填。

6、发送消息使用的网络类型 - 字典值，必填，仅限“公网”或“DCN”，默认初始是“DCN”！

##### 出参：
本次发送是否成功 - string格式。

