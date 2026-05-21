from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
USER_FILE_DIR = BASE_DIR / "user_files" / "inbox"

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".xlsx",
    ".docx",
    ".pptx",
    ".html",
    ".htm",
}


def ensure_file_library_exists():
    USER_FILE_DIR.mkdir(parents=True, exist_ok=True)

def list_user_files() -> list[Path]:
    ensure_file_library_exists()
    files = []
    for path in USER_FILE_DIR.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        files.append(path)
    files.sort(key=lambda item: item.name.lower())
    return files

def format_file_list() -> str:
    files = list_user_files()
    if not files:
        return (
            f"当前文件夹里没有可读取文件。\n"
            f"请把 PDF、TXT、CSV、XLSX、DOCX、PPTX 等文件放进：\n"
            f"{USER_FILE_DIR}"
        )
    lines = [f"当前文件夹：{USER_FILE_DIR}", ""]
    for index, path in enumerate(files, start=1):
        size_kb = path.stat().st_size / 1024
        lines.append(f"{index}. {path.name} ({size_kb:.1f} KB)")
    return "\n".join(lines)

def get_file_by_index(index: int) -> Path | None:
    files = list_user_files()
    if index < 1 or index > len(files):
        return None
    return files[index - 1]