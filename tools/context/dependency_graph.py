import ast
from pathlib import Path
from typing import Optional

def _extract_python_imports(file_path: str) -> dict:
    imports = {"stdlib": [], "third_party": [], "internal": []}
    stdlib_modules = {'os', 'sys', 'json', 'time', 're', 'collections', 'typing', 'pathlib', 'asyncio', 'subprocess', 'dataclasses', 'enum'}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module in stdlib_modules:
                        imports["stdlib"].append(alias.name)
                    else:
                        imports["third_party"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module in stdlib_modules:
                        imports["stdlib"].append(node.module)
                    elif node.level > 0:
                        imports["internal"].append(node.module)
                    else:
                        imports["third_party"].append(node.module)
    except SyntaxError:
        pass
    return imports

async def get_dependency_graph(root_path: str, file_path: str) -> dict:
    try:
        root = Path(root_path)
        target = root / file_path
        if not target.exists():
            return {"success": False, "error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {file_path}"}}
        imports = _extract_python_imports(str(target))
        return {"success": True, "data": {"file": file_path, "dependencies": imports, "dependents": []}}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}
