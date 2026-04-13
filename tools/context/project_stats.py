import os
from pathlib import Path
from collections import defaultdict
from typing import Optional

LANGUAGE_EXTENSIONS = {
    "python": [".py"], "javascript": [".js", ".jsx"], "typescript": [".ts", ".tsx"],
    "go": [".go"], "java": [".java"], "rust": [".rs"], "ruby": [".rb"],
    "cpp": [".cpp", ".cc", ".hpp"], "c": [".c", ".h"],
}

def _detect_language(file_path: str) -> Optional[str]:
    ext = Path(file_path).suffix.lower()
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if ext in exts:
            return lang
    return None

def _count_lines(file_path: str) -> int:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except:
        return 0

async def get_project_stats(root_path: str) -> dict:
    try:
        root = Path(root_path)
        if not root.exists():
            return {"success": False, "error": {"code": "PATH_NOT_FOUND", "message": f"Path not found: {root_path}"}}
        exclude_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'target', 'build'}
        total_files = 0
        total_lines = 0
        language_stats = defaultdict(lambda: {"files": 0, "lines": 0})
        for item in root.rglob("*"):
            if item.is_file():
                if any(excluded in str(item) for excluded in exclude_dirs):
                    continue
                total_files += 1
                lines = _count_lines(str(item))
                total_lines += lines
                lang = _detect_language(str(item))
                if lang:
                    language_stats[lang]["files"] += 1
                    language_stats[lang]["lines"] += lines
        return {"success": True, "data": {"total_files": total_files, "total_lines": total_lines, "languages": dict(language_stats)}}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}
