from collections import deque


class ChatSessionManager:
    def __init__(self, max_messages_per_contact: int = 12):
        self.max_messages_per_contact = max_messages_per_contact
        self.sessions = {}

    def get_session(self, contact: str) -> dict:
        if contact not in self.sessions:
            self.sessions[contact] = {
                "seen_keys": set(),
                "processed_ai_texts": set(),
                "messages": deque(maxlen=self.max_messages_per_contact),
            }
        return self.sessions[contact]

    def has_seen(self, contact: str, message_key: str) -> bool:
        session = self.get_session(contact)
        return message_key in session["seen_keys"]

    def mark_seen(self, contact: str, message_key: str):
        session = self.get_session(contact)
        session["seen_keys"].add(message_key)

    def has_processed_ai_text(self, contact: str, text: str) -> bool:
        session = self.get_session(contact)
        return text in session["processed_ai_texts"]

    def mark_processed_ai_text(self, contact: str, text: str):
        session = self.get_session(contact)
        session["processed_ai_texts"].add(text)

    def add_user_message(self, contact: str, content: str):
        session = self.get_session(contact)
        session["messages"].append({
            "role": "user",
            "content": content,
        })

    def add_assistant_message(self, contact: str, content: str):
        session = self.get_session(contact)
        session["messages"].append({
            "role": "assistant",
            "content": content,
        })

    def build_messages(self, contact: str, system_prompt: str, current_prompt: str) -> list[dict]:
        session = self.get_session(contact)
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]
        messages.extend(list(session["messages"]))
        messages.append({
            "role": "user",
            "content": current_prompt,
        })
        return messages