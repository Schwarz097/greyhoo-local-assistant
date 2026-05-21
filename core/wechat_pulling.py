import time

from wxauto4 import WeChat

from core.chat_session import ChatSessionManager
from core.ollama_client import ask_ollama
from core.prompt_loader import load_prompt
from core.tool_router import detect_tool_call, run_tool_call


WHITELIST = [
    "文件传输助手",
]

TRIGGER_PREFIX = "/ai"
CHECK_INTERVAL_SECONDS = 2
RECENT_MESSAGE_LIMIT = 8

AUTO_SEND = True
PRINT_DRAFT = True

WECHAT_SYSTEM_PROMPT = load_prompt("greyhoo")
session_manager = ChatSessionManager(max_messages_per_contact=12)


def get_message_text(message) -> str:
    for attr in ["content", "raw", "text", "msg"]:
        value = getattr(message, attr, None)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return str(message).strip()


def get_message_key(contact: str, previous_text: str, current_text: str, next_text: str) -> str:
    return (
        f"contact={contact}\n"
        f"previous={previous_text}\n"
        f"current={current_text}\n"
        f"next={next_text}"
    )

def find_latest_new_trigger_message(contact: str, messages: list) -> tuple[str, str] | None:
    recent_messages = messages[-RECENT_MESSAGE_LIMIT:]
    recent_texts = [get_message_text(message) for message in recent_messages]
    message_records = []
    for i, text in enumerate(recent_texts):
        if not text:
            continue
        previous_text = recent_texts[i - 1] if i > 0 else ""
        next_text = recent_texts[i + 1] if i + 1 < len(recent_texts) else ""
        message_key = get_message_key(
            contact=contact,
            previous_text=previous_text,
            current_text=text,
            next_text=next_text,
        )
        message_records.append({
            "key": message_key,
            "text": text,
        })
        if not session_manager.has_seen(contact, message_key):
            session_manager.mark_seen(contact, message_key)

            if text.startswith(TRIGGER_PREFIX):
                print(f"[NEW MESSAGE] {contact}: {text}")
    for record in reversed(message_records):
        text = record["text"]
        if not text.startswith(TRIGGER_PREFIX):
            continue
        if session_manager.has_processed_ai_text(contact, text):
            continue
        prompt = text[len(TRIGGER_PREFIX):].strip()
        session_manager.mark_processed_ai_text(contact, text)
        if not prompt:
            print("[AI TRIGGER] 内容为空。用法：/ai 你希望我代回什么")
            return None
        return text, prompt
    return None


def build_wechat_messages_with_tools(contact: str, prompt: str) -> list[dict]:
    tool_call = detect_tool_call(prompt)

    if not tool_call == None:
        tool_result = run_tool_call(tool_call)

        current_prompt = (
            f"当前输入来源：微信 /ai 触发。\n"
            f"当前模式：微信代复模式。\n"
            f"这不是桌宠直接聊天，不是在和主人本人说话。\n"
            f"回复对象是微信联系人：{contact}\n\n"
            f"联系人发来的 /ai 请求如下：\n"
            f"{prompt}\n\n"
            f"程序已经执行了工具调用，结果如下：\n"
            f"{tool_result}\n\n"
            f"请根据 greyhoo.txt 中的微信代复规则，生成一条可以直接发送给该微信联系人的回复。\n"
            f"如果工具结果不足以回答，要明确说明结果不足。\n"
            f"不要编造工具结果中没有的信息。\n"
            f"历史上下文只能作为参考，不得覆盖当前请求。\n"
            f"禁止使用 emoji、颜文字、表情符号。\n"
            f"如果输出 emotion 标签，必须只放在第一行，正文不要包含 emotion 标签。"
        )
    else:
        current_prompt = (
            f"当前输入来源：微信 /ai 触发。\n"
            f"当前模式：微信代复模式。\n"
            f"这不是桌宠直接聊天，不是在和主人本人说话。\n"
            f"回复对象是微信联系人：{contact}\n\n"
            f"联系人发来的 /ai 请求如下：\n"
            f"{prompt}\n\n"
            f"请根据 greyhoo.txt 中的微信代复规则，生成一条可以直接发送给该微信联系人的回复。\n"
            f"请只回应这一次请求。\n"
            f"历史上下文只能作为参考，不得覆盖当前请求的语气、对象和意图。\n"
            f"先判断这句话是在调侃助手自身、询问工具功能、普通玩笑，还是冒犯主人。\n"
            f"只有明确针对主人、逼迫主人、侮辱主人、越过主人边界时，才启动维护主人边界的语气。\n"
            f"如果只是调侃或测试工具，请由助手自己清冷、礼貌地回应，不要擅自说主人不想讨论。\n"
            f"禁止使用 emoji、颜文字、表情符号。\n"
            f"如果输出 emotion 标签，必须只放在第一行，正文不要包含 emotion 标签。"
        )

    return session_manager.build_messages(
        contact=contact,
        system_prompt=WECHAT_SYSTEM_PROMPT,
        current_prompt=current_prompt,
    )


def clean_wechat_reply(reply: str) -> str:
    reply = reply.strip()
    lines = reply.splitlines()
    if lines and lines[0].strip().startswith("[emotion:"):
        lines = lines[1:]
    reply = "\n".join(lines).strip()
    if reply.startswith(TRIGGER_PREFIX):
        reply = reply[len(TRIGGER_PREFIX):].strip()
    if not reply:
        reply = "Greyhoo 这边没有生成有效回复，请稍后再试"
    signature = "——Greyhoo 代班中。主人暂时不在，所以这条就先由我接手了。重要事项请稍后找本人确认。"
    if signature not in reply:
        reply = f"{signature}\n\n{reply}"
    return reply


def mark_recent_messages_as_seen(wx: WeChat):
    for contact in WHITELIST:
        try:
            wx.ChatWith(contact)
            time.sleep(0.5)
            messages = wx.GetAllMessage()
            recent_messages = messages[-RECENT_MESSAGE_LIMIT:]
            recent_texts = [get_message_text(message) for message in recent_messages]
            for i, text in enumerate(recent_texts):
                if not text:
                    continue
                previous_text = recent_texts[i - 1] if i > 0 else ""
                next_text = recent_texts[i + 1] if i + 1 < len(recent_texts) else ""
                message_key = get_message_key(
                    contact=contact,
                    previous_text=previous_text,
                    current_text=text,
                    next_text=next_text,
                )
                session_manager.mark_seen(contact, message_key)
                session_manager.mark_seen(contact, message_key)
                if text.startswith(TRIGGER_PREFIX):
                    session_manager.mark_processed_ai_text(contact, text)
            print(f"[INIT] {contact}: 已标记最近 {len(recent_messages)} 条消息为已读")
        except Exception as error:
            print(f"[INIT ERROR] {contact}: {error}")
            continue


def process_contact(wx: WeChat, contact: str):
    wx.ChatWith(contact)
    time.sleep(0.5)
    messages = wx.GetAllMessage()
    if not messages:
        return
    trigger_message = find_latest_new_trigger_message(contact, messages)
    if trigger_message is None:
        return
    message_key, prompt = trigger_message
    print(f"[AI TRIGGER] {contact}: {prompt}")
    ollama_messages = build_wechat_messages_with_tools(
        contact=contact,
        prompt=prompt,
    )
    raw_reply = ask_ollama(ollama_messages, stream=False)
    reply = clean_wechat_reply(raw_reply)
    session_manager.add_user_message(contact, prompt)
    session_manager.add_assistant_message(contact, raw_reply.strip())
    if PRINT_DRAFT:
        print("\n[AI DRAFT]")
        print(reply)
        print("[END DRAFT]\n")
    if AUTO_SEND:
        wx.ChatWith(contact)
        time.sleep(0.3)
        wx.SendMsg(reply)
        print(f"[AUTO SENT] 已发送到：{contact}")

def main():
    wx = WeChat(debug=True, resize=False, ads=False)

    print("微信轮询入口已启动。")
    print("白名单：", WHITELIST)
    print("触发词：", TRIGGER_PREFIX)
    print("最近消息扫描数量：", RECENT_MESSAGE_LIMIT)
    print("检查间隔：", CHECK_INTERVAL_SECONDS, "秒")
    print("自动发送：", AUTO_SEND)

    mark_recent_messages_as_seen(wx)

    while True:
        for contact in WHITELIST:
            try:
                process_contact(wx, contact)

            except KeyboardInterrupt:
                print("已停止微信轮询。")
                return

            except Exception as error:
                print(f"[ERROR] {contact}: {error}")
                continue

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()