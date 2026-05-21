from pathlib import Path

from docling.document_converter import DocumentConverter


MAX_FILE_CHARS = 12000
def read_file_with_docling(file_path: str, max_chars: int = MAX_FILE_CHARS) -> str:
    path = Path(file_path).expanduser()
    if not path.exists():
        return f"文件不存在：{path}"
    if not path.is_file():
        return f"这不是一个文件：{path}"
    try:
        converter = DocumentConverter()
        result = converter.convert(str(path))
        document = result.document
        markdown = document.export_to_markdown()
        markdown = markdown.strip()
        if not markdown:
            return f"文件已读取，但没有提取到文本内容：{path}"
        if len(markdown) > max_chars:
            markdown = (
                markdown[:max_chars]
                + "\n\n[内容过长，已截断。当前只展示前 "
                + str(max_chars)
                + " 个字符。]"
            )
        return markdown
    except Exception as error:
        return f"读取文件时出错：{error}"