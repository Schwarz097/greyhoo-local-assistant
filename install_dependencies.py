import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(command: list[str]):
    print(">", " ".join(command))
    subprocess.check_call(command)


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ is required. Python 3.11 is recommended.")

    requirements = ROOT / "requirements.txt"

    if not requirements.exists():
        raise FileNotFoundError(f"requirements.txt not found: {requirements}")

    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install", "-r", str(requirements)])

    inbox = ROOT / "user_files" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / ".gitkeep").touch(exist_ok=True)

    prompts = ROOT / "prompts"
    prompts.mkdir(parents=True, exist_ok=True)

    assets = ROOT / "assets" / "character"
    assets.mkdir(parents=True, exist_ok=True)

    if shutil.which("ollama") is None:
        print()
        print("[WARNING] Ollama was not found in PATH.")
        print("Install Ollama manually from: https://ollama.com/download/windows")
        print("Then pull or create the model used by MODEL_NAME in main.py and core/ollama_client.py.")
    else:
        print()
        print("[OK] Ollama command found.")

    print()
    print("Dependency installation finished.")


if __name__ == "__main__":
    main()
