import sys
import threading
import time
import webbrowser
import socket
import os
import traceback
from pathlib import Path


def ensure_streamlit_credentials() -> None:
    """避免首次启动时 Streamlit 交互式邮箱提示阻塞进程。"""
    user_streamlit_dir = Path.home() / ".streamlit"
    user_streamlit_dir.mkdir(parents=True, exist_ok=True)
    credentials_file = user_streamlit_dir / "credentials.toml"

    if not credentials_file.exists():
        credentials_file.write_text("[general]\nemail = \"\"\n", encoding="utf-8")


def wait_for_server(host: str, port: int, timeout_seconds: float = 30.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.8)
            try:
                sock.connect((host, port))
                return True
            except Exception:
                time.sleep(0.3)
    return False


def open_browser_when_ready(url: str, host: str, port: int) -> None:
    def _task() -> None:
        if wait_for_server(host, port, timeout_seconds=35.0):
            webbrowser.open(url, new=2)

    threading.Thread(target=_task, daemon=True).start()


def resolve_app_file() -> Path:
    candidates = []

    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "streamlit_app.py")
        candidates.append(Path(sys.executable).resolve().parent / "streamlit_app.py")

    candidates.append(Path(__file__).resolve().parent / "streamlit_app.py")

    for p in candidates:
        if p.exists():
            return p

    raise FileNotFoundError("未找到 streamlit_app.py，请在打包时包含该文件。")


def show_error_message(message: str) -> None:
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "悟空GitHub数据分析工具 - 启动失败", 0x10)
    except Exception:
        pass


def main() -> None:
    project_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    app_file = resolve_app_file()
    host = "localhost"
    port = 8501
    url = f"http://{host}:{port}"

    ensure_streamlit_credentials()
    open_browser_when_ready(url, host, port)

    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ.update(env)

    try:
        from streamlit.web import cli as stcli

        sys.argv = [
            "streamlit",
            "run",
            str(app_file),
            "--server.headless",
            "true",
            "--server.address",
            host,
            "--server.port",
            str(port),
            "--browser.gatherUsageStats",
            "false",
            "--global.developmentMode",
            "false",
        ]

        stcli.main()
    except Exception:
        error_text = traceback.format_exc()
        log_file = project_dir / "wukong_github_collector_error.log"
        try:
            log_file.write_text(error_text, encoding="utf-8")
        except Exception:
            pass
        show_error_message(f"启动失败，错误日志已写入：\n{log_file}")
        raise


if __name__ == "__main__":
    main()