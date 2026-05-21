import json
import requests


OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "ilunaz-qwen"


def ask_ollama(messages: list[dict], stream: bool = False) -> str:
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": stream,
    }
    if stream:
        return _ask_ollama_stream(url, payload)
    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]

def _ask_ollama_stream(url: str, payload: dict) -> str:
    full_reply = ""
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
            if data.get("done"):
                break
    return full_reply