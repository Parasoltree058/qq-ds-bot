# -*- coding: utf-8 -*-
import asyncio
import os
import botpy
from botpy import logging
from botpy.message import DirectMessage, Message, GroupMessage
from botpy.ext.cog_yaml import read
import chat2ai


test_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))

_log = logging.get_logger()


class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_direct_message_create(self, message: DirectMessage):
        env = "single"
        if message.content.startswith("/图片"):
            _log.info(f"收到{env}请求图片消息")
            sending_content = chat2ai.chat(message, env)
            file_path = sending_content
            await asyncio.sleep(2)
            try:
                await self.api.post_dms(
                    guild_id=message.guild_id,
                    file_image=file_path,  # 字符串路径
                    msg_id=message.id
                )
                _log.info(f"图片消息已发送")
            except Exception as e:
                # 打印异常到控制台和日志
                _log.error(f"处理图片消息时出现异常：{e}")
                await self.api.post_dms(
                    guild_id=message.guild_id,
                    content=f"呜呜，不知道怎么发图片！({e})",
                    msg_id=message.id,
                )


        else:
            _log.info(f"收到普通{env}消息")
            sending_content = chat2ai.chat(message, env)
            sending_content = sending_content.strip() # 去除前后空格或换行
            try:
                await self.api.post_dms(
                    guild_id=message.guild_id,
                    content=f"{sending_content}",
                    msg_id=message.id,
                )
                _log.info(f"消息发送成功")
            except Exception as e:
                _log.error(f"消息发送失败{e}")
                await self.api.post_dms(
                    guild_id=message.guild_id,
                    content=f"\n\n发送消息失败，请重试或者换用图片模式\n{e}",
                    msg_id=message.id,
                )


    async def on_group_at_message_create(self, message: GroupMessage):
        env = "group"
        if message.content.startswith(" /图片"):
            _log.info(f"收到{env}请求图片消息")
            sending_content = chat2ai.chat(message, env)
            MAX_RETRIES = 5
            file_url = sending_content
            await asyncio.sleep(2)

            # 这里需要重新设计逻辑，最好能重试两次
            uploadMedia = None
            for attempt in range(MAX_RETRIES):
                try:
                    uploadMedia = await message._api.post_group_file(
                        group_openid=message.group_openid,
                        file_type=1,  # 根据接口文档指定文件类型，例如：1=图片
                        url=file_url
                    )
                    if uploadMedia:
                        break
                except Exception as e:
                    _log.warning(f"上传文件失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(1)  # 等待1秒后重试
                    else:
                        raise e  # 如果多次失败，抛出异常

            try:
                if not uploadMedia:
                    raise RuntimeError("文件上传失败，`uploadMedia` 为 None")
                # 资源上传后，会得到Media，用于发送消息
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=7,  # 7表示富媒体类型
                    msg_id=message.id,
                    media=uploadMedia
                )
                _log.info(f"图片消息已发送")
            except Exception as e:
                # 打印异常到控制台和日志
                _log.error(f"处理图片消息时出现异常：{e}")
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0,
                    msg_id=message.id,
                    content=f"呜呜，不知道怎么发图片！({e})"
                )


        else:
            _log.info(f"收到普通{env}消息")
            sending_content = chat2ai.chat(message, env)
            try:
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0,
                    msg_id=message.id,
                    content=f"{sending_content}"
                )
                _log.info(f"消息发送成功")
            except Exception as e:
                _log.error(f"消息发送失败{e}")
                await message._api.post_group_message(
                    group_openid=message.group_openid,
                    msg_type=0,
                    msg_id=message.id,
                    content=f"\n\n发送消息失败，请重试或者换用图片模式\n{e}"
                )



if __name__ == "__main__":

    intents = botpy.Intents(direct_message=True, public_guild_messages=True, public_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
