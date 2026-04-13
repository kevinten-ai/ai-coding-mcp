import ast
import time
from pathlib import Path
from typing import Optional
from config import config
from utils.cache import FileCache

def _extract_python_symbols(file_path: str) -> list:
    symbols = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append({"name": node.name, "type": "function", "line": node.lineno, "file": file_path})
            elif isinstance(node, ast.ClassDef):
                symbols.append({"name": node.name, "type": "class", "line": node.lineno, "file": file_path})
    except SyntaxError:
        pass
    return symbols

def _should_index_file(file_path: str) -> bool:
    exclude_patterns = ['__pycache__', '.git', 'node_modules', 'venv', '.venv']
    return not any(pattern in file_path for pattern in exclude_patterns)

async def index_project(root_path: str, language: str = "python") -> dict:
    try:
        root = Path(root_path)
        if not root.exists():
            return {"success": False, "error": {"code": "PATH_NOT_FOUND", "message": f"Path not found: {root_path}"}}
        cache = FileCache(str(root / ".ai-coding-mcp-cache"), ttl=config.cache.ttl)
        cache_key = f"index_{root_path}_{language}"
        cached = cache.get(cache_key)
        if cached:
            return {"success": True, "data": cached}
        symbols = []
        files_count = 0
        if language == "python":
            for py_file in root.rglob("*.py"):
                if _should_index_file(str(py_file)):
                    file_symbols = _extract_python_symbols(str(py_file))
                    symbols.extend(file_symbols)
                    files_count += 1
        else:
            return {"success": False, "error": {"code": "UNSUPPORTED_LANGUAGE", "message": f"Language '{language}' not yet supported"}}
        result = {"symbols": symbols, "files_count": files_count, "timestamp": time.time()}
        cache.set(cache_key, result)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}

async def get_symbol_info(root_path: str, symbol_name: str) -> dict:
    index_result = await index_project(root_path)
    if not index_result["success"]:
        return index_result
    for symbol in index_result["data"]["symbols"]:
        if symbol["name"] == symbol_name:
            return {"success": True, "data": symbol}
    return {"success": False, "error": {"code": "SYMBOL_NOT_FOUND", "message": f"Symbol '{symbol_name}' not found"}}
