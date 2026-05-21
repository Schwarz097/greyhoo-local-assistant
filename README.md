# Deskoppet / Greyhoo Local AI Assistant

Deskoppet is a local-first desktop AI assistant prototype built around **PySide6 + Ollama**. It explores a small application-layer AI workflow: a desktop pet UI, emotion-based avatar switching, local LLM chat, explicit tool routing, document ingestion, web search, and an experimental Windows WeChat `/ai` polling entry.

This project is not a model-training project. It is an **AI application integration project**: local model deployment, prompt modes, tool routing, file reading, UI interaction, and controlled automation.

> Status: early prototype. The code is useful for learning and demonstration, but still needs cleanup before production use.

## Features

- Local desktop pet UI based on PySide6.
- Local LLM backend through Ollama.
- Character prompt loaded from `prompts/greyhoo.txt`.
- Emotion tag parsing and avatar switching.
- Tool routing:
  - `/search <query>`: web search through `ddgs`.
  - `/file list`: list files in `user_files/inbox`.
  - `/file <index> <question>`: read a selected file through Docling.
- Runtime-only chat session cache.
- Experimental WeChat polling mode through `wxauto4`.

## Architecture

```text
main.py                      Desktop pet UI entry
core/
  ollama_client.py           Shared Ollama API client
  tool_router.py             /search and /file tool router
  web_search.py              ddgs web search wrapper
  file_reader.py             Docling document reader
  file_library.py            user_files/inbox file list
  chat_session.py            runtime short-term session cache
  prompt_loader.py           prompt loader
  wechat_polling.py          optional WeChat /ai polling entry
prompts/
  greyhoo.txt                character / behavior prompt
assets/
  character/
    emotion_smile.png
    emotion_thinking.png
    emotion_talking.png
    emotion_happy.png
    emotion_hurt.png
    emotion_angry.png
user_files/
  inbox/                     local files for /file tool
```

## Requirements

### External software

1. **Python 3.10+**  
   Python 3.11 is recommended.

2. **Ollama**  
   Install Ollama from the official website:

   https://ollama.com/download/windows

   After installation, start Ollama and pull or create a model. This project currently expects:

   ```text
   ilunaz-qwen
   ```

   You can change this in:

   - `main.py`
   - `core/ollama_client.py`

3. **Windows WeChat 4.1.8.107** for the optional WeChat integration  
   The current tested Windows WeChat version is:

   ```text
   4.1.8.107
   ```

   Windows WeChat version archive:

   https://github.com/cscnk52/wechat-windows-versions

   The WeChat feature is optional. The desktop pet and file/search tools can run without it.

### Python packages

Install dependencies:

```powershell
pip install -r requirements.txt
```

Or run:

```powershell
python install_dependencies.py
```

## Ollama setup

Make sure Ollama is running locally:

```powershell
ollama list
```

If your model name is different, update:

```python
MODEL_NAME = "your-model-name"
```

in:

```text
main.py
core/ollama_client.py
```

Ollama is expected to listen on:

```text
http://localhost:11434
```

Do not expose Ollama to the public internet unless you understand the security risk.

## Running the desktop pet

```powershell
python main.py
```

Right-click the pet window to quit.

## Tool commands

### Web search

```text
/search wxauto4 WeChat 4.1.8 support
```

The tool is defined in:

```text
core/tool_router.py
core/web_search.py
```

### File reader

Put files into:

```text
user_files/inbox
```

Supported extensions are defined in `core/file_library.py`.

List available files:

```text
/file list
```

Read the first file:

```text
/file 1 summarize this document
```

The file reader uses Docling and is defined in:

```text
core/file_reader.py
```

Docling may download OCR/layout models on first use and cache them locally.

## Replacing the character prompt

The default character prompt is:

```text
prompts/greyhoo.txt
```

To replace the character:

1. Put your new prompt in:

   ```text
   prompts/your_character.txt
   ```

2. Change the prompt loader in:

   ```text
   main.py
   core/wechat_polling.py
   ```

   Search for:

   ```python
   load_prompt("greyhoo")
   ```

   Replace it with:

   ```python
   load_prompt("your_character")
   ```

The prompt should keep the emotion output rule unless you also change the code:

```text
[emotion: smile]
[emotion: thinking]
[emotion: talking]
[emotion: happy]
[emotion: hurt]
[emotion: angry]
```

## Replacing emotion images

Emotion images are stored in:

```text
assets/character/
```

Use these exact filenames unless you also edit `EMOTION_IMAGE_PATHS` in `main.py`:

```text
emotion_smile.png
emotion_thinking.png
emotion_talking.png
emotion_happy.png
emotion_hurt.png
emotion_angry.png
```

The avatar display size is controlled in `main.py`:

```python
PET_IMAGE_SIZE = 220
WINDOW_WIDTH = 397
WINDOW_HEIGHT = 500
```

## Optional WeChat `/ai` polling mode

The WeChat entry is experimental and Windows-only.

Run:

```powershell
python -m core.wechat_polling
```

or, if the file is still named `wechat_pulling.py` in your local copy:

```powershell
python -m core.wechat_pulling
```

### Trigger

Only messages that start with `/ai` are processed.

Examples:

```text
/ai 帮我回复一句晚点看
/ai /search wxauto4 微信 4.1.8 支持情况
/ai /file list
/ai /file 1 summarize this file
```

### Warning

The free `wxauto4` workflow works by controlling the visible Windows WeChat client. During polling, the desktop WeChat window may:

- stay visible or jump to foreground,
- switch between contacts in the whitelist,
- flicker while checking chats,
- interfere with normal manual WeChat use.

This is expected behavior for the current prototype. It is not silent background monitoring.

### Whitelist

The whitelist should be configured locally and should not be committed to GitHub.

Current prototype file:

```text
core/wechat_polling.py
```

Search for:

```python
WHITELIST = [...]
```

For public GitHub, keep only safe placeholders, for example:

```python
WHITELIST = ["文件传输助手"]
```

## Privacy notes

- Files are read from `user_files/inbox` unless you explicitly pass a path.
- The project does not intentionally upload files.
- Ollama runs locally by default.
- `ddgs` web search uses online search services.
- Docling may download models and cache them locally.
- WeChat polling logs and cache files should never be committed.

## Before uploading to GitHub

Delete these:

```text
.idea/
__pycache__/
core/__pycache__/
wxauto_logs/
core/wxauto_logs/
*.log
```

Do not commit:

```text
config.local.py
user_files/inbox/*
real WeChat contacts
private documents
local model files
API keys
```

Keep:

```text
user_files/inbox/.gitkeep
```

## Related projects / dependencies

- Ollama: https://ollama.com/
- Ollama GitHub: https://github.com/ollama/ollama
- Docling: https://github.com/docling-project/docling
- Docling docs: https://docling-project.github.io/docling/
- ddgs: https://github.com/deedy5/ddgs
- wxauto: https://github.com/cluic/wxauto
- wxauto4: https://github.com/cluic/wxauto4
- Windows WeChat archive: https://github.com/cscnk52/wechat-windows-versions

## Disclaimer

This project is for local personal experimentation and learning. The WeChat automation feature depends on Windows WeChat UI behavior and may break across versions. Do not use it for spam, harassment, commercial automation, or any unauthorized messaging workflow.
