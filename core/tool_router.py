from core.web_search import web_search, format_search_results
from core.file_reader import read_file_with_docling
from core.file_library import format_file_list, get_file_by_index


SEARCH_PREFIX = "/search"
FILE_PREFIX = "/file"

def detect_tool_call(user_text: str) -> dict | None:
    text = user_text.strip()
    if text.startswith(SEARCH_PREFIX):
        query = text[len(SEARCH_PREFIX):].strip()
        if not query:
            return {
                "tool": "web_search",
                "error": "搜索内容为空。用法：/search 你要搜索的内容",
            }
        return {
            "tool": "web_search",
            "query": query,
        }
    if text.startswith(FILE_PREFIX):
        rest = text[len(FILE_PREFIX):].strip()
        if not rest or rest.lower() == "list":
            return {
                "tool": "file_list",
            }
        file_target, question = split_file_command(rest)
        if not file_target:
            return {
                "tool": "file_list",
            }
        if file_target.isdigit():
            return {
                "tool": "file_reader_by_index",
                "index": int(file_target),
                "question": question or "请总结这个文件。",
            }
        return {
            "tool": "file_reader_by_path",
            "file_path": file_target,
            "question": question or "请总结这个文件。",
        }
    return None


def split_file_command(rest: str) -> tuple[str, str]:
    rest = rest.strip()
    if not rest:
        return "", ""
    if rest.startswith('"'):
        end_index = rest.find('"', 1)
        if end_index == -1:
            return rest.strip('"'), ""
        file_target = rest[1:end_index].strip()
        question = rest[end_index + 1:].strip()
        return file_target, question
    parts = rest.split(maxsplit=1)
    file_target = parts[0].strip()
    question = parts[1].strip() if len(parts) > 1 else ""
    return file_target, question


def run_tool_call(tool_call: dict) -> str:
    if tool_call.get("error"):
        return tool_call["error"]
    tool_name = tool_call.get("tool")
    if tool_name == "web_search":
        query = tool_call.get("query", "").strip()
        if not query:
            return "搜索内容为空。"
        print("[TOOL CALL] web_search:", query)
        results = web_search(query, max_results=5)
        return format_search_results(results)
    if tool_name == "file_list":
        print("[TOOL CALL] file_list")
        return format_file_list()
    if tool_name == "file_reader_by_index":
        index = tool_call.get("index")
        question = tool_call.get("question", "请总结这个文件。")
        path = get_file_by_index(index)
        if path is None:
            return f"没有找到编号为 {index} 的文件。请先使用 /file list 查看文件列表。"
        print("[TOOL CALL] file_reader:", path)
        print("[FILE QUESTION]", question)
        content = read_file_with_docling(str(path))
        return (
            f"文件名：{path.name}\n"
            f"文件路径：{path}\n"
            f"用户问题：{question}\n\n"
            f"文件内容如下：\n"
            f"{content}"
        )
    if tool_name == "file_reader_by_path":
        file_path = tool_call.get("file_path", "").strip()
        question = tool_call.get("question", "请总结这个文件。")
        if not file_path:
            return "文件路径为空。"
        print("[TOOL CALL] file_reader:", file_path)
        print("[FILE QUESTION]", question)
        content = read_file_with_docling(file_path)
        return (
            f"文件路径：{file_path}\n"
            f"用户问题：{question}\n\n"
            f"文件内容如下：\n"
            f"{content}"
        )
    return f"未知工具：{tool_name}"