ALLOWED_EMOTIONS = {
    "normal",
    "smile",
    "thinking",
    "surprised",
    "angry",
    "sleepy",
}


def parse_emotion_and_reply(text: str) -> tuple[str, str]:
    lines = text.strip().splitlines()
    if not lines:
        return "normal", ""
    first_line = lines[0].strip()
    if first_line.startswith("[emotion:") and first_line.endswith("]"):
        emotion = first_line[len("[emotion:"):-1].strip()
        if emotion in ALLOWED_EMOTIONS:
            reply = "\n".join(lines[1:]).strip()
            return emotion, reply
    return "normal", text.strip()