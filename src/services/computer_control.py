"""通过聊天执行白名单内的本地命令（传统龙虾「操控电脑」能力）。"""

import re
import shlex
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from src.utils.config import get_settings
from src.utils.logger import log


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _get_allowed_commands() -> set:
    s = get_settings()
    raw = getattr(s, "allowed_commands", "") or "ls,pwd,date,whoami"
    return {c.strip().lower() for c in raw.split(",") if c.strip()}


def _parse_command_from_message(message: str) -> Optional[list]:
    """
    从用户消息中解析出要执行的命令（列表形式，便于 subprocess）。
    支持：「运行 ls」「执行 pwd」「帮我跑一下 ls -la」「运行 ls -la」等。
    """
    msg = (message or "").strip()
    if not msg:
        return None
    msg_norm = msg
    for trigger in ["运行", "执行", "跑一下", "跑", "帮我运行", "帮我执行", "帮我跑", "运行命令", "执行命令"]:
        if trigger in msg_norm:
            msg_norm = msg_norm.split(trigger, 1)[-1].strip()
            break
    if not msg_norm:
        return None
    # 简单按空格分，若需支持引号可用 shlex
    try:
        parts = shlex.split(msg_norm)
    except ValueError:
        parts = msg_norm.split()
    if not parts:
        return None
    return parts


def run_command_safe(message: str) -> Tuple[bool, str]:
    """
    若消息为「运行/执行 xxx」且 xxx 在白名单内，则执行并返回 (True, 输出)；
    否则返回 (False, 说明信息)。
    """
    settings = get_settings()
    if not getattr(settings, "enable_computer_control", False):
        return False, "当前未开启「聊天操控电脑」功能。请在 .env 中设置 ENABLE_COMPUTER_CONTROL=true 并配置 ALLOWED_COMMANDS 后重启服务。"

    allowed = _get_allowed_commands()
    parts = _parse_command_from_message(message)
    if not parts:
        return False, "未识别到要执行的命令。可以说：运行 ls、执行 pwd、帮我跑一下 date 等。"

    base = parts[0].lower()
    if base not in allowed:
        return False, f"命令「{base}」不在允许列表中（当前允许：{', '.join(sorted(allowed))}）。如需开放更多命令，请在 .env 中配置 ALLOWED_COMMANDS。"

    cwd = _project_root()
    timeout = 15
    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            timeout=timeout,
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        if result.returncode != 0 and err:
            out = f"{out}\n[stderr]\n{err}" if out else f"[stderr]\n{err}"
        if result.returncode != 0:
            out = f"[退出码 {result.returncode}]\n{out}"
        log.info(f"Computer control executed: {parts} -> returncode={result.returncode}")
        return True, out or "(无输出)"
    except subprocess.TimeoutExpired:
        log.warning(f"Computer control timeout: {parts}")
        return True, f"命令已超时（{timeout} 秒），已终止。"
    except FileNotFoundError:
        return True, f"未找到命令：{parts[0]}"
    except Exception as e:
        log.exception(f"Computer control error: {e}")
        return True, f"执行出错：{e}"
