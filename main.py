import sys
import json
import re
from pathlib import Path

import requests

from core.prompt_loader import load_prompt
from core.tool_router import detect_tool_call, run_tool_call

from PySide6.QtCore import Qt, QPoint, QThread, Signal
from PySide6.QtGui import QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QMenu,
)


BASE_DIR = Path(__file__).resolve().parent
CHARACTER_DIR = BASE_DIR / "assets" / "character"

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "ilunaz-qwen"

PET_IMAGE_SIZE = 220
CHAT_BOX_WIDTH = 360
CHAT_BOX_HEIGHT = 170
WINDOW_WIDTH = 397
WINDOW_HEIGHT = 500

EMOTION_IMAGE_PATHS = {
    "smile": CHARACTER_DIR / "emotion_smile.png",
    "thinking": CHARACTER_DIR / "emotion_thinking.png",
    "talking": CHARACTER_DIR / "emotion_talking.png",
    "happy": CHARACTER_DIR / "emotion_happy.png",
    "hurt": CHARACTER_DIR / "emotion_hurt.png",
    "angry": CHARACTER_DIR / "emotion_angry.png",
}

DEFAULT_EMOTION = "smile"

EMOTION_PATTERN = re.compile(
    r"\[emotion:\s*(smile|thinking|talking|happy|hurt|angry)\]",
    re.IGNORECASE,
)

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)


def load_desktop_prompt() -> str:
    try:
        return load_prompt("greyhoo")
    except Exception as greyhoo_error:
        print(f"[PROMPT WARNING] greyhoo.txt 读取失败{greyhoo_error}")
    return (
        "你是一个本地桌宠助手。\n"
        "每次回复第一行必须输出 [emotion: smile]、[emotion: thinking]、"
        "[emotion: talking]、[emotion: happy]、[emotion: hurt] 或 [emotion: angry]。\n"
        "emotion 标签必须单独占第一行。正文禁止使用 emoji。"
    )

DESKTOP_PROMPT = load_desktop_prompt()

def clean_display_reply(full_reply: str) -> tuple[str, str]:
    if not full_reply:
        return DEFAULT_EMOTION, "嗯……刚才没有收到有效回复。"
    match = EMOTION_PATTERN.search(full_reply)
    emotion = match.group(1).lower() if match else DEFAULT_EMOTION
    if emotion not in EMOTION_IMAGE_PATHS:
        emotion = DEFAULT_EMOTION
    clean_reply = EMOTION_PATTERN.sub("", full_reply)
    clean_reply = EMOJI_PATTERN.sub("", clean_reply)
    lines = []
    for line in clean_reply.splitlines():
        line = line.strip()
        if not line:
            continue
        lines.append(line)
    clean_reply = "\n".join(lines).strip()
    if not clean_reply:
        clean_reply = "嗯……刚才那句没组织好。再说一遍？"
    return emotion, clean_reply


class OllamaWorker(QThread):
    token_received = Signal(str)
    finished_received = Signal(str)
    error_received = Signal(str)
    def __init__(self, messages):
        super().__init__()
        self.messages = messages
    def run(self):
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": MODEL_NAME,
            "messages": self.messages,
            "stream": True,
        }
        full_reply = ""
        try:
            with requests.post(url, json=payload, stream=True, timeout=120) as response:
                response.raise_for_status()
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    data = json.loads(line)
                    message = data.get("message", {})
                    content = message.get("content", "")
                    if content:
                        full_reply += content
                        self.token_received.emit(content)
                    if data.get("done"):
                        break
            self.finished_received.emit(full_reply)
        except requests.exceptions.ConnectionError:
            self.error_received.emit("连不上 Ollama。请确认 Ollama 正在运行。")
        except requests.exceptions.HTTPError as error:
            self.error_received.emit(f"Ollama HTTP 错误：{error}")
        except Exception as error:
            self.error_received.emit(f"调用 Ollama 时出错：{error}")


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.messages = [
            {
                "role": "system",
                "content": DESKTOP_PROMPT,
            }
        ]
        self.worker = None
        self.current_reply = ""
        self.drag_position = QPoint()
        self.setWindowTitle("Greyhoo Desktop Pet")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.pet_label = QLabel()
        self.pet_label.setAlignment(Qt.AlignCenter)
        self.pet_label.setFixedSize(PET_IMAGE_SIZE, PET_IMAGE_SIZE)
        self.current_emotion = DEFAULT_EMOTION
        self.load_emotion_image(DEFAULT_EMOTION)
        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_box.setFixedWidth(CHAT_BOX_WIDTH)
        self.chat_box.setFixedHeight(CHAT_BOX_HEIGHT)
        self.chat_box.setStyleSheet("""
            QTextEdit {
                color: white;
                background-color: rgba(20, 20, 20, 190);
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("输入一句话……")
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.setStyleSheet("""
            QLineEdit {
                color: white;
                background-color: rgba(30, 30, 30, 220);
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: rgba(70, 70, 70, 220);
                border: none;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: rgba(100, 100, 100, 230);
            }
        """)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)
        layout = QVBoxLayout()
        layout.addWidget(self.pet_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.chat_box, alignment=Qt.AlignCenter)
        layout.addLayout(input_layout)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.setLayout(layout)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

    def load_emotion_image(self, emotion: str):
        if emotion not in EMOTION_IMAGE_PATHS:
            emotion = DEFAULT_EMOTION
        image_path = EMOTION_IMAGE_PATHS[emotion]
        if not image_path.exists():
            print(f"[IMAGE ERROR] 找不到表情图片: {image_path}")
            image_path = EMOTION_IMAGE_PATHS[DEFAULT_EMOTION]
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            print(f"[IMAGE ERROR] 图片读取失败: {image_path}")
            self.pet_label.setText("图片读取失败")
            self.pet_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: rgba(0, 0, 0, 180);
                    border-radius: 12px;
                    padding: 8px;
                }
            """)
            return
        self.current_emotion = emotion
        self.pet_pixmap = pixmap
        scaled_pixmap = pixmap.scaled(
            PET_IMAGE_SIZE,
            PET_IMAGE_SIZE,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.pet_label.setPixmap(scaled_pixmap)

    def set_emotion(self, emotion: str):
        self.load_emotion_image(emotion)

    def append_message(self, speaker: str, text: str):
        self.chat_box.append(f"{speaker}：{text}")
        self.chat_box.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_box.ensureCursorVisible()

    def remove_last_thinking_line(self):
        text = self.chat_box.toPlainText()
        marker = "思考中……"
        if marker not in text:
            return
        lines = text.splitlines()
        for index in range(len(lines) - 1, -1, -1):
            if lines[index] == marker:
                del lines[index]
                break
        self.chat_box.setPlainText("\n".join(lines))
        self.chat_box.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_box.ensureCursorVisible()

    def build_desktop_user_content(self, text: str) -> str:
        tool_call = detect_tool_call(text)
        if tool_call is not None:
            tool_result = run_tool_call(tool_call)
            return (
                f"当前输入来源：桌宠直接对话。\n"
                f"这不是微信代复任务。\n\n"
                f"用户发起了一个工具请求。\n\n"
                f"原始用户输入：{text}\n\n"
                f"工具返回结果：\n"
                f"{tool_result}\n\n"
                f"请基于工具返回结果回答用户。\n"
                f"如果工具结果不足以回答，要明确说明结果不足。\n"
                f"不要编造工具结果中没有的信息。\n"
                f"禁止使用 emoji、颜文字、表情符号。"
            )
        return (
            f"当前输入来源：桌宠直接对话。\n"
            f"这不是微信代复任务。\n\n"
            f"用户输入：{text}\n\n"
            f"禁止使用 emoji、颜文字、表情符号。\n"
            f"emotion 标签必须单独占第一行。"
        )

    def send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return
        if self.worker is not None and self.worker.isRunning():
            self.append_message("系统", "她还在回你，先等一下。")
            return
        self.input_box.clear()
        self.append_message("你", text)
        self.append_message("桌宠", "思考中……")
        user_content = self.build_desktop_user_content(text)
        self.messages.append({
            "role": "user",
            "content": user_content,
        })
        self.current_reply = ""
        self.worker = OllamaWorker(self.messages.copy())
        self.worker.token_received.connect(self.on_token_received)
        self.worker.finished_received.connect(self.on_finished_received)
        self.worker.error_received.connect(self.on_error_received)
        self.worker.start()

    def on_token_received(self, token):
        self.current_reply += token

    def on_finished_received(self, full_reply):
        emotion, clean_reply = clean_display_reply(full_reply)
        print("raw_reply =", full_reply)
        print("emotion =", emotion)
        print("clean_reply =", clean_reply)
        self.set_emotion(emotion)
        self.remove_last_thinking_line()
        self.append_message("桌宠", clean_reply)
        self.messages.append({
            "role": "assistant",
            "content": full_reply,
        })
        system_message = self.messages[0]
        recent_messages = self.messages[-16:]
        self.messages = [system_message] + [
            message for message in recent_messages
            if message["role"] != "system"
        ]

    def on_error_received(self, error_message):
        self.remove_last_thinking_line()
        self.append_message("系统", error_message)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        quit_action = menu.addAction("退出")
        action = menu.exec(event.globalPos())
        if action == quit_action:
            QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    pet = DesktopPet()
    pet.show()

    sys.exit(app.exec())
