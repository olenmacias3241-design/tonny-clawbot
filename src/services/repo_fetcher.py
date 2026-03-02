"""拉取指定 GitHub 仓库到本地缓存，供文档与代码分析使用。"""

import re
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from src.utils.logger import log
from src.utils.config import get_settings


def _repos_cache_root() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    return root / "repos_cache"


def normalize_repo(repo: str) -> Tuple[str, str]:
    """将 'owner/repo' 或 'owner@gmail/repo' 规范为 (owner, repo)。"""
    repo = (repo or "").strip()
    if "/" in repo:
        owner, name = repo.split("/", 1)
        owner = re.sub(r"@.*$", "", owner).strip()
        return owner.strip(), name.strip()
    return "", ""


def get_repo_path(owner: str, repo: str) -> Path:
    """返回该仓库在本地缓存中的路径（不执行拉取）。"""
    safe = f"{owner}_{repo}".replace("/", "_")
    return _repos_cache_root() / safe


def _clone_url(owner: str, repo: str) -> str:
    """带认证的 clone URL：若配置了 GITHUB_TOKEN 则用于私有仓库。"""
    token = getattr(get_settings(), "github_token", None)
    if token and token.strip():
        return f"https://x-access-token:{token.strip()}@github.com/{owner}/{repo}.git"
    return f"https://github.com/{owner}/{repo}.git"


def ensure_repo_cloned(owner: str, repo: str) -> Path:
    """
    确保仓库已克隆到 repos_cache/owner_repo，若不存在则 git clone --depth 1。
    私有仓库需在 .env 中配置 GITHUB_TOKEN。
    返回仓库根目录 Path。
    """
    path = get_repo_path(owner, repo)
    if path.is_dir() and (path / ".git").is_dir():
        return path
    cache_root = _repos_cache_root()
    cache_root.mkdir(parents=True, exist_ok=True)
    url = _clone_url(owner, repo)
    log.info(f"Cloning repo for docs: {owner}/{repo} -> {path}")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(path)],
            check=True,
            capture_output=True,
            timeout=120,
            cwd=str(cache_root),
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or b"").decode("utf-8", errors="replace")
        log.error(f"Git clone failed: {err}")
        if "Authentication failed" in err or "could not read Username" in err or "403" in err:
            raise ValueError(
                "克隆失败（认证失败）：若为私有仓库，请在 .env 中配置 GITHUB_TOKEN（GitHub Personal Access Token）"
            ) from e
        raise ValueError(f"克隆仓库失败: {owner}/{repo}") from e
    except FileNotFoundError:
        raise ValueError("未找到 git 命令，请先安装 Git") from None
    return path


def read_guide_from_repo(repo_root: Path) -> Optional[str]:
    """从仓库中读取说明文档：优先根目录的 PROJECT_GUIDE.md / README.md，否则搜索全目录。"""
    # 1) 先看根目录
    for name in ("PROJECT_GUIDE.md", "README.md"):
        p = repo_root / name
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                log.warning(f"Read {p}: {e}")

    # 2) 全目录搜索：先找任意 PROJECT_GUIDE.md，再找任意 README.md（按路径排序，优先浅层）
    def _skip(p: Path) -> bool:
        parts = p.parts
        return ".git" in parts or "__pycache__" in parts or "node_modules" in parts

    for name in ("PROJECT_GUIDE.md", "README.md"):
        candidates = sorted(
            (p for p in repo_root.rglob(name) if p.is_file() and not _skip(p)),
            key=lambda x: (len(x.parts), str(x)),
        )
        for p in candidates:
            try:
                return p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                log.warning(f"Read {p}: {e}")
    return None
