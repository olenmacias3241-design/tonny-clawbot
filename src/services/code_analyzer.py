"""代码分析服务：扫描仓库，提取各模块、类、函数及其功能说明。"""

import ast
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def _get_docstring(node: ast.AST) -> str:
    """从 AST 节点提取 docstring。"""
    doc = ast.get_docstring(node)
    return (doc or "").strip()


def _analyze_file(file_path: Path, root: Path) -> Optional[Dict[str, Any]]:
    """分析单个 Python 文件，提取模块、类、函数信息。"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return None

    rel_path = str(file_path.relative_to(root))
    module_doc = _get_docstring(tree)

    classes: List[Dict[str, Any]] = []
    functions: List[Dict[str, Any]] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [
                {"name": n.name, "doc": _get_docstring(n)}
                for n in node.body
                if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
            ]
            classes.append({
                "name": node.name,
                "doc": _get_docstring(node),
                "methods": methods[:8],
            })
        elif isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "doc": _get_docstring(node),
            })

    return {
        "path": rel_path,
        "module_doc": module_doc,
        "classes": classes,
        "functions": functions[:12],  # 最多 12 个模块级函数
    }


def analyze_codebase(
    src_root: Optional[Path] = None,
    section_descriptions: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    分析整个代码库，按板块（目录）分组返回各模块功能。

    返回结构：
    {
        "sections": { "bot": [...], ... },
        "section_descriptions": { "bot": "...", ... },
        "root": str
    }
    """
    if src_root is None:
        src_root = Path(__file__).resolve().parent.parent

    if section_descriptions is None:
        section_descriptions = {
            "bot": "AI 对话：多模型接入、对话上下文管理",
            "models": "数据模型：请求/响应、活动、通知等 Pydantic 模型",
            "handlers": "API 路由：FastAPI 端点、请求处理",
            "services": "业务服务：活动落库、日报生成、代码分析",
            "providers": "外部数据源：GitHub API 等",
            "utils": "工具：配置、日志、邮件/Telegram/WhatsApp 发送",
            "root": "根模块：数据库、入口等",
        }

    sections: Dict[str, List[Dict[str, Any]]] = {}
    seen_files = set()

    for py_file in src_root.rglob("*.py"):
        if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
            continue
        rel = py_file.relative_to(src_root)
        parts = rel.parts
        if len(parts) >= 2:
            section = parts[0]
        else:
            section = "root"  # src/db.py, src/__init__.py 等

        if section not in sections:
            sections[section] = []
        seen_files.add(str(py_file))

        result = _analyze_file(py_file, src_root)
        if result:
            sections[section].append(result)

    # 未在默认描述中的目录，补上通用描述
    section_descriptions = dict(section_descriptions)
    for sec in sections:
        if sec not in section_descriptions:
            section_descriptions[sec] = f"目录: {sec}"

    # 按路径排序
    for key in sections:
        sections[key].sort(key=lambda x: x["path"])

    return {
        "sections": sections,
        "section_descriptions": section_descriptions,
        "root": str(src_root),
    }
