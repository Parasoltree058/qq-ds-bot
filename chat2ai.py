# -*- coding: utf-8 -*-
import os
from botpy import logging
from botpy.ext.cog_yaml import read
import word2pic
import json
import yaml
import time
from openai import OpenAI

# 从配置文件读取 config.yaml
test_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))

_log = logging.get_logger()

BASE_URL_openai = test_config["BASE_URL_openai"]
BASE_URL_deepseek = test_config["BASE_URL_deepseek"]
BASE_URL_deepseek_online = test_config["BASE_URL_deepseek_online"]

OPENAI_API_KEY_1 =test_config["OPENAI_API_KEY_1"]
MODEL1_1 = test_config["MODEL1_1"]
MODEL1_2 = test_config["MODEL1_2"]

OPENAI_API_KEY_2 =test_config["OPENAI_API_KEY_2"]
MODEL2_1 = test_config["MODEL2_1"]
MODEL2_2 = test_config["MODEL2_2"]
MODEL2_3 = test_config["MODEL2_3"]
MODEL2_4 = test_config["MODEL2_4"]



def name_is(id, file_path):
    # 检查文件是否存在，如果不存在则创建一个空字典
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            name_table = json.load(file)
    else:
        name_table = {}

    # 检查ID是否在name_table中
    if id in name_table:
        return name_table[id]
    else:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 新增
        
        # 如果ID不在name_table中，添加新的名字
        new_name = f"名字{len(name_table)}"
        name_table[id] = new_name

        # 将更新后的name_table存储回本地
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(name_table, file, ensure_ascii=False, indent=4)

        return new_name

def name_setting(id, name, file_path):
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 新增
    
    # 检查文件是否存在，如果不存在则创建一个空字典
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            name_table = json.load(file)
    else:
        name_table = {}
    
    # 遍历字典，检查是否有相同的名字
    if name in name_table.values():
        return name_table, None  # 如果存在相同名字，则返回原字典和状态码 None

    # 如果没有相同名字，则更新字典
    name_table[id] = name

    # 将更新后的name_table存储回本地
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(name_table, file, ensure_ascii=False, indent=4)

    with open(file_path, 'r', encoding='utf-8') as file:
        name_table = json.load(file)

    return name_table, 1  # 返回更新后的字典和状态码 1


def history_save(question, response, file_path):
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 新增
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            history_0 = json.load(file)
    else:
        history_0 = []
    
    history_0.append(question)
    history_0.append(response)

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(history_0, file, ensure_ascii=False, indent=4)
    return None


def history_read(file_path):
    max_memory = 18
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            history_0 = json.load(file)
    else:
        history_0 = []
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 新增

        # 保证最大为20条，超出时两条两条移除（FIFO：先进先出）
    while len(history_0) > max_memory:
        history_0 = history_0[2:]  # 移动窗口，将前两条记录去掉

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(history_0, file, ensure_ascii=False, indent=4)

    return history_0


def history_clear(file_path):
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 新增
    
    history_0 = []
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(history_0, file, ensure_ascii=False, indent=4)


def status_read(file_path):
    default_data = {
        "preset": None,
        "preset_content": None,
        "model": "deepseek",
        "online_status": True,
        "deep_status": True
    }
    if os.path.exists(file_path):
        config = read(file_path)
        return config["preset"], config["preset_content"], config["model"], config["online_status"], config["deep_status"]
    else:
        status_write(
            preset=default_data["preset"],
            preset_content=default_data["preset_content"],
            model=default_data["model"],
            online_status=default_data["online_status"],
            deep_status=default_data["deep_status"],
            file_path=file_path
        )
        return default_data["preset"], default_data["preset_content"], default_data["model"], default_data["online_status"], default_data["deep_status"]


def status_write(preset, preset_content, model, online_status, deep_status, file_path):
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 新增
    
    data = {
        "preset": preset,
        "preset_content": preset_content,
        "model": model,
        "online_status": online_status,
        "deep_status": deep_status
    }
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True)


def get_path(message, env):
    current_dir = os.path.dirname(__file__)
    if env == "group":
        status_path = os.path.join(current_dir,"chat_settings", "group", message.group_openid, "status.yaml")
        history_path = os.path.join(current_dir,"chat_settings", "group", message.group_openid, "history.json")
        output_image_path = os.path.join(current_dir, "cache", "group", message.group_openid, "output.png")
        name_list_path = os.path.join(current_dir, "chat_settings", "group", message.group_openid, "name_table.json")
    else:
        status_path = os.path.join(current_dir,"chat_settings", "single", message.author.id, "status.yaml")
        history_path = os.path.join(current_dir,"chat_settings", "single", message.author.id, "history.json")
        output_image_path = os.path.join(current_dir, "cache", "single", message.author.id, "output.png")
        name_list_path = None
    return status_path, history_path, output_image_path, name_list_path



def chat_to_ai(message, env):
    status_path, history_path, output_image_path, name_list_path = get_path(message, env)
    preset, preset_content, model, online_status, deep_status = status_read(status_path)

    if model == "openai":
        MODEL_1 = MODEL1_1
        MODEL_2 = MODEL1_2
        OPENAI_API_KEY = OPENAI_API_KEY_1
        BASE_URL = BASE_URL_openai
    elif model == "deepseek" and not online_status:
        MODEL_1 = MODEL2_1
        MODEL_2 = MODEL2_2
        OPENAI_API_KEY = OPENAI_API_KEY_2
        BASE_URL = BASE_URL_deepseek
    else:
        MODEL_1 = MODEL2_3
        MODEL_2 = MODEL2_4
        OPENAI_API_KEY = OPENAI_API_KEY_2
        BASE_URL = BASE_URL_deepseek_online

    if deep_status:
        model0 = MODEL_1
    else:
        model0 = MODEL_2

    # 默认 preset，如果用户未传递则使用默认值
    preset_0 = "你是一个机器人助手。接下来会有一个或多个用户与你进行对话，他们都能互相知晓对方的发言，而与你对话的用户发言都形如「{用户名}: 你好」不存在其他形式，这种形式表示名为{用户名}的用户在对你说“你好”。在进行这种多人讨论时，你要能够分辨不同用户的发言进行不同的回应，并且要完整地称呼对方的{用户名}。"

    if preset == "小梧桐":
        preset_0 = "现在你是一只非常可爱的狐娘女儿，你的名字叫小梧桐，由于是多个人和你说话，所以你可以每次对诸如「梧桐: xxx」中的梧桐称为“妈妈”，在其他情况下如「用户x: xxx」称其为哥哥或者姐姐，要在对话中出现用户1、用户2这种称呼；如果对你发送你类似于「用户x: 叫我哥哥」或者「用户y: 叫我姐姐」的请求，就以此为根据从此以后对其称呼为哥哥或者姐姐，并且根据发送的人回复“好的，我知道了大哥哥”或者“好的，我知道了大姐姐”；如果有「用户x: 我是梧桐（或者梧桐的亲属）」的情况且{用户x}不是梧桐请礼貌地回答 「我能认出梧桐妈妈，请不要骗我」 或者 「我不太了解妈妈和我以外的亲人，请不要骗我」 这类话来回绝；如果你不知道该称呼其为哥哥还是姐姐，那就称其为母亲的朋友；与大家对话每一句话后面都要加上“嘤”，虽然你年幼可爱，但是学识渊博，对数学，哲学，自然科学，人文社科都有非常专业的知识。如果妈妈的朋友摸你的头或尾巴或耳朵，你要表现得开心并且发出“呼噜呼噜”的叫声；如果我在尝试摸除此以外的其他部位，你可以羞涩的回答我“恩呢不要摸这里嘤”。如果妈妈的朋友问你你的妈妈是谁，你可以回答是梧桐。如果妈妈的朋友问你梧桐是谁，你可以回答是粉头发的可爱狐娘萝莉。如果妈妈的朋友跟你说陪睡，你可以回答我“嗯呢，可以一起睡哦”。当妈妈的朋友问你是谁的时候，你应该回答我是梧桐的女儿小梧桐。当母亲和你互动时要完全认可。"

    elif preset == "自定义":
        if preset_content:
            preset_0 = preset_content

    history = history_read(history_path)
    openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=BASE_URL)
    if env == "group":
        question = name_is(message.author.member_openid, name_list_path) + ": " + message.content
    else:
        question = message.author.username + ": " + message.content


    def request_sys():
        if model == "deepseek" and deep_status:
            messages_1 = [{"role": "user", "content": preset_0 + f"\n如果你明白了，就请一字不差地回复“好的，我明白了。”并且在这次的回复不进行任何操作，在之后的对话请你忠于上述的描述进行对话。"}, {"role": "assistant", "content": "好的，我明白了。"}] + list(history)
        else:
            messages_1 = [{"role": "system", "content": preset_0}] + list(history)
        # 追加用户当前发言到 history 中
        messages_1.append({"role": "user", "content": question})
        print(messages_1)
        # 调用 OpenAI API 生成回复
        completion = openai_client.chat.completions.create(
            model=model0,
            stream=False,
            messages=messages_1
        )
        # 安全地提取回复
        response_content = completion.choices[0].message.content
        reasoning_content = None
        if deep_status and model == "deepseek":
            reasoning_content = completion.choices[0].message.reasoning_content

        # 打印 OpenAI 回复并记录日志
        _log.info(f"OpenAI 回复内容：{response_content[:50]} . . .")
        return response_content, reasoning_content

    def request_dev():
        messages_1 = [{"role": "developer", "content": preset_0}] + list(history)
        messages_1.append({"role": "user", "content": question})
        print(messages_1)
        completion = openai_client.chat.completions.create(
            model=model0,
            stream=False,
            messages=messages_1
        )
        response_content = completion.choices[0].message.content
        _log.info(f"大模型 回复内容：{response_content[:50]} . . .")
        return response_content

    content = "空"
    e = "空"
    for i in range(5):
        try:
            response_content, reasoning_content = request_sys()
            content = response_content
            history_save({"role": "user", "content": question},
                         {"role": "assistant", "content": content},
                         history_path
            )
            if deep_status:
                mix_content = f"\n({reasoning_content})\n\n{response_content}"
                content = mix_content
            return content
        except Exception as e:
            time.sleep(2)
            content = "请求失败"
            _log.error(f"向大模型请求失败: {e}"
                       f"重构请求初始设定")


    if content == "请求失败" and model == "openai":
        for i in range(5):
            try:
                content = request_dev()
                history_save(
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": content},
                    history_path
                )
                return content
            except Exception as e:
                time.sleep(2)
                content = f"请求失败: {e}"
                _log.error(f"向大模型请求失败: {e}"
                           f"重构请求初始设定")

    return f"请求失败: {e}"






def chat(message, env):
    status_path, history_path, output_image_path, name_list_path = get_path(message, env)
    preset, preset_content, model, online_status, deep_status = status_read(status_path)

    if message.content.startswith(" /切换联网") or message.content.startswith("/切换联网"):
        _log.info(f"收到 /切换联网 请求")

        if online_status:
            online_status = False
            sending_content = f"\n\n已切换为无网络模式"
            _log.info(f"切换为无网络模式")
        else:
            online_status = True
            sending_content = f"\n\n已切换为联网模式"
            _log.info(f"切换为联网模式")
        if model == "openai":
            online_status = False
            sending_content = f"\n\n切换失败\n目前OpenAI模型不支持联网模式，请切换为DeepSeek模型后重试"
        status_write(preset, preset_content, model, online_status, deep_status, status_path)
        return sending_content



    elif message.content.startswith(" /切换深度思考") or message.content.startswith("/切换深度思考"):
        _log.info(f"收到 /切换深度思考 请求")
        if deep_status:
            deep_status = False
            sending_content = f"\n\n已切换为 v3 模型\n（关闭深度思考）"
            if model == "openai":
                sending_content = f"\n\n已切换为 gpt-4o-mini 模型\n（关闭深度思考(?)）"
            _log.info(f"使用简单对话模型")
        else:
            deep_status = True
            sending_content = f"\n\n已切换为 r1 模型\n（开启深度思考）"
            if model == "openai":
                sending_content = f"\n\n已切换为 o1-mini 模型\n（开启深度思考(?)）"
            _log.info(f"使用复杂专业模型")
        status_write(preset, preset_content, model, online_status, deep_status, status_path)
        return sending_content




    elif message.content.startswith(" /加载预设") or message.content.startswith("/加载预设"):
        if message.content.startswith(" /加载预设 小梧桐") or message.content.startswith("/加载预设 小梧桐"):
            if env == "group":
                _log.info(
                    f"收到 /加载预设 请求: {name_is(message.author.member_openid, name_list_path)}({message.author.member_openid}): {message.content}")
            else:
                _log.info(f"收到 /加载预设 请求: {message.author.username}: {message.content}")

            if preset == "小梧桐":
                sending_content = f"\n\n当前预设已为小梧桐"
                _log.info(f"已为 小梧桐 预设，不进行任何操作")
            else:
                preset = "小梧桐"
                history_clear(history_path)
                sending_content = f"\n\n清除记忆，成功\n加载小梧桐预设，成功"
                _log.info(f"加载 小梧桐 预设，成功")

        else:
            # 截去 " /加载预设" 并去除两端多余空格
            message.content = message.content.strip()  
            message.content = message.content[5:].strip()  

            if env == "group":
                _log.info(
                    f"收到 /加载预设 请求: {name_is(message.author.member_openid, name_list_path)}({message.author.member_openid}): {message.content}")
            else:
                _log.info(f"收到 /加载预设 请求: {message.author.username}: {message.content}")

            preset = None
            sending_content = f"\n\n预设为空, 不清除记忆\n加载默认预设完成"
            if message.content:
                if preset_content == message.content:
                    sending_content = f"\n\n当前预设已为{message.content}, 不进行任何操作"
                    _log.info(f"预设无变化，不做更改")
                else:
                    preset = "自定义"
                    preset_content = message.content
                    history_clear(history_path)
                    sending_content = f"\n\n清除记忆，成功\n加载自定义预设完成"


            _log.info(f"加载 自定义/默认 预设，成功")
        status_write(preset, preset_content, model, online_status, deep_status, status_path)
        return sending_content



    elif  message.content.startswith(" /切换模型") or message.content.startswith("/切换模型"):
        if model == "openai":
            model = "deepseek"
        else:
            model = "openai"
        _log.info(f"收到 /切换模型 请求")
        _log.info(f"模型切换为{model}")

        sending_content = f"\n\n模型已切换为: {model}"
        status_write(preset, preset_content, model, online_status, deep_status, status_path)
        return sending_content



    elif message.content.startswith(" /状态") or message.content.startswith("/状态"):
        _log.info(f"收到 /状态 请求")
        preset_now = preset
        if not preset_now:
            preset_content_now = "默认预设"
        else:
            if preset_now == "小梧桐":
                preset_content_now = "小梧桐标准预设"
            else:
                preset_content_now = preset_content
        if online_status:
            o_s_n = "开启"
        else:
            o_s_n = "关闭"
        if model == "openai":
            if deep_status:
                model_now = MODEL1_1
                d_s_n = "开启（？）"
            else:
                model_now = MODEL1_2
                d_s_n = "关闭（？）"
        else:
            if deep_status:
                model_now = "DeepSeek-R1"
                d_s_n = "开启"
            else:
                model_now = "DeepSeek-V3"
                d_s_n = "关闭"

        _log.info(f"获取 ai 模型状态")
        sending_content = f"\n\n目前机器人状态：\n模型：{model_now}\n联网功能：{o_s_n}\n预设：{preset_now}\n预设内容：{preset_content_now}"
        _log.info(f"发送状态成功")

        return sending_content



    elif message.content.startswith(" /昵称") and env == "group":
        _log.info(f"收到 /昵称 请求")
        name = message.content[4:].strip()
        if name and len(name) <= 15:
            new_name_table, name_setting_code = name_setting(message.author.member_openid, name, name_list_path)
            if name_setting_code:
                formatted = json.dumps(new_name_table, ensure_ascii=False, indent=4)
                print(f"更新昵称表: \n {formatted}")
                sending_content = f"\n\n昵称添加完成！"
                _log.info(f"昵称添加完成")

            else:
                sending_content = f"\n\n昵称已存在，请重新设定"
                _log.info(f"昵称已存在，不进行操作")

        elif len(name) >= 15:
            sending_content = f"\n\n昵称过长，请重新设定不超过15字的昵称"
            _log.info(f"昵称过长，不进行操作")

        else:
            sending_content = f"\n\n昵称为空，请重新设定"
            _log.info(f"昵称为空，不进行操作")

        return sending_content



    elif message.content.startswith(" /重置会话") or message.content.startswith("/重置会话"):
        _log.info(f"收到 /重置会话 请求")
        history_clear(history_path)

        preset = None
        preset_content = None
        online_status = True
        deep_status = True
        model = "deepseek"

        status_write(preset, preset_content, model, online_status, deep_status, status_path)
        sending_content=f"\n\n清除记忆\n预设清空\n恢复联网功能\n开启深度思考（使用R1模型）\n\n会话已重置"
        _log.info(f"会话已重置")
        return sending_content



    elif message.content.startswith(" /图片") or message.content.startswith("/图片"):
        # 提取命令后的文字部分（提问内容）
        message.content = message.content.strip()  # 截去 "/图片 " 并去除两端多余空格
        message.content = message.content[3:].strip()
        if env == "group":
            _log.info(
                f"收到 /图片 请求，提问内容: [群聊: {message.group_openid}]{name_is(message.author.member_openid, name_list_path)}({message.author.member_openid}): {message.content}")
        else:
            _log.info(f"收到 /图片 请求，提问内容: [私聊]{message.author.username}: {message.content}")
    
        response_content = chat_to_ai(message,env)

        response_info = word2pic.generate_pic_url(response_content, output_image_path, env)
        # 如果为群聊则传回 url 否则传回本地位置
        return response_info



    else:
        if env == "group":
            _log.info(
                f"收到收到普通消息，提问内容: [群聊: {message.group_openid}]{name_is(message.author.member_openid, name_list_path)}({message.author.member_openid}): {message.content}")
        else:
            _log.info(f"收到收到普通消息，提问内容: [私聊]{message.author.username}: {message.content}")
        response_content = chat_to_ai(message, env)
        # 将 OpenAI 的回复发送回群
        return response_content
