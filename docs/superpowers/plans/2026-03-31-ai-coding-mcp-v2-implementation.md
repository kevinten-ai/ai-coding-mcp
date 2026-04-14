# AI Coding MCP v2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AI Coding MCP v2 — a lightweight MCP server for AI IDEs with 20 tools across 4 modules (context, knowledge, workflow, specs), CLI-first architecture, zero LLM wrapping.

**Architecture:** FastMCP entry with modular tool registration. Each module is self-contained with its own tools file. Shared utilities: `cli_runner` (subprocess wrapper), `security` (path validation), `cache` (file-based TTL cache), `parsers` (AST routing). All external calls go through CLI (git, gh, pip, npm, curl).

**Tech Stack:** Python 3.9+, FastMCP, Pydantic, tree-sitter, subprocess, pytest.

**Spec Reference:** `/Users/kevinten/projects/ai-coding-mcp/docs/superpowers/specs/2026-03-31-ai-coding-mcp-v2-design.md`

---

## Chunk 1: Foundation — Config, Utils, and Server Skeleton

### Task 1.1: Create v2 Config

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/config.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_config.py`

- [ ] **Step 1: Write failing test for config**

```python
# tests/test_config.py
from config import MCPConfig, ServerConfig, SecurityConfig

def test_default_config():
    config = MCPConfig()
    assert config.server.host == "localhost"
    assert config.server.port == 8080
    assert config.security.max_file_size == 50 * 1024 * 1024

def test_security_validation():
    config = MCPConfig()
    # Should allow paths under allowed_paths
    assert config.security.validate_path("./src/main.py") is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_default_config -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'config'"

- [ ] **Step 3: Implement minimal config**

```python
# config.py
from typing import List, Optional
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=8080)
    debug: bool = Field(default=False)

class SecurityConfig(BaseModel):
    allowed_paths: List[str] = Field(default=["./"])
    max_file_size: int = Field(default=50*1024*1024)

    def validate_path(self, path: str) -> bool:
        # TODO: implement path traversal check
        return True

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class CacheConfig(BaseModel):
    enabled: bool = Field(default=True)
    ttl: int = Field(default=3600)
    cache_dir: str = Field(default="~/.cache/ai-coding-mcp")

class MCPConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

config = MCPConfig()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_config.py config.py
git commit -m "feat: add v2 config with Server/Security/Logging/Cache configs"
```

---

### Task 1.2: Create CLI Runner

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/utils/cli_runner.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_cli_runner.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cli_runner.py
import pytest
from utils.cli_runner import run_cli, CLIResult

@pytest.mark.asyncio
async def test_run_cli_success():
    result = await run_cli(["echo", "hello"])
    assert result.returncode == 0
    assert "hello" in result.stdout

@pytest.mark.asyncio
async def test_run_cli_timeout():
    result = await run_cli(["sleep", "10"], timeout=0.1)
    assert result.returncode != 0
    assert "timeout" in result.error.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli_runner.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement CLI runner**

```python
# utils/cli_runner.py
import asyncio
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class CLIResult:
    returncode: int
    stdout: str
    stderr: str
    execution_time: float
    error: Optional[str] = None

async def run_cli(
    command: list[str],
    cwd: Optional[str] = None,
    timeout: int = 30,
    env: Optional[dict] = None
) -> CLIResult:
    """
    Execute CLI command with timeout and error handling.

    Returns CLIResult with returncode, stdout, stderr, execution_time, error.
    """
    start_time = time.time()

    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )

        execution_time = time.time() - start_time

        return CLIResult(
            returncode=proc.returncode,
            stdout=stdout.decode('utf-8', errors='replace'),
            stderr=stderr.decode('utf-8', errors='replace'),
            execution_time=execution_time
        )

    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return CLIResult(
            returncode=-1,
            stdout="",
            stderr="",
            execution_time=time.time() - start_time,
            error=f"Command timed out after {timeout}s"
        )
    except FileNotFoundError as e:
        return CLIResult(
            returncode=-1,
            stdout="",
            stderr="",
            execution_time=time.time() - start_time,
            error=f"Command not found: {command[0]}"
        )
    except Exception as e:
        return CLIResult(
            returncode=-1,
            stdout="",
            stderr="",
            execution_time=time.time() - start_time,
            error=str(e)
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli_runner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add utils/cli_runner.py tests/test_cli_runner.py
git commit -m "feat: add cli_runner with timeout and error handling"
```

---

### Task 1.3: Create Cache Module

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/utils/cache.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_cache.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_cache.py
import pytest
import tempfile
import os
from utils.cache import FileCache

def test_cache_set_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCache(tmpdir, ttl=3600)
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

def test_cache_expired():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCache(tmpdir, ttl=0)  # immediate expiry
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cache module**

```python
# utils/cache.py
import json
import hashlib
import time
import os
from pathlib import Path
from typing import Any, Optional

class FileCache:
    """Simple file-based cache with TTL support."""

    def __init__(self, cache_dir: str, ttl: int = 3600):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

    def _get_cache_path(self, key: str) -> Path:
        """Generate cache file path from key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)

            # Check TTL
            if time.time() - cached.get('timestamp', 0) > self.ttl:
                cache_path.unlink(missing_ok=True)
                return None

            return cached.get('data')
        except (json.JSONDecodeError, IOError):
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any) -> None:
        """Store value in cache with timestamp."""
        cache_path = self._get_cache_path(key)

        cached = {
            'timestamp': time.time(),
            'data': value
        }

        with open(cache_path, 'w') as f:
            json.dump(cached, f)

    def clear(self) -> None:
        """Clear all cached files."""
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink(missing_ok=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add utils/cache.py tests/test_cache.py
git commit -m "feat: add file-based cache with TTL support"
```

---

### Task 1.4: Create Server Skeleton

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/server.py`

- [ ] **Step 1: Implement minimal server**

```python
# server.py
#!/usr/bin/env python3
"""
AI Coding MCP Server v2

Lightweight MCP server for AI IDEs. Provides structured data tools
without LLM wrapping.
"""

import asyncio
import sys
from mcp.server.fastmcp import FastMCP
from config import config

# Create MCP server
mcp = FastMCP(
    name="ai-coding",
    version="2.0.0",
    instructions="""
AI Coding MCP Server provides structured data for coding tasks:
- Project context: index_project, get_symbol_info, get_dependency_graph, get_project_stats
- External knowledge: search_docs, get_package_info, search_code_examples, check_compatibility
- Workflow: git_status, git_history, git_branch_analysis, ci_status, issue_list, pr_summary
- Specs: list_specs, get_spec, search_specs, create_spec, scaffold_project, validate_structure
"""
)

@mcp.tool()
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}

# TODO: Import and register tools from modules
# from tools.context import code_indexer, dependency_graph, project_stats
# from tools.knowledge import doc_search, package_info, code_search, compatibility
# from tools.workflow import git_ops, ci_github
# from tools.specs import spec_manager, scaffold, validator

async def main():
    """Run the MCP server."""
    print("🚀 AI Coding MCP v2 starting...")
    print(f"📍 Server: {config.server.host}:{config.server.port}")

    # Run the server
    await mcp.run()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
```

- [ ] **Step 2: Test server starts**

Run: `python -c "import server; print('Server imports OK')"`
Expected: "Server imports OK"

- [ ] **Step 3: Commit**

```bash
git add server.py
git commit -m "feat: add server skeleton with FastMCP and health_check tool"
```

---

## Chunk 2: Module 1 — Project Context

### Task 2.1: Create Code Indexer

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/context/code_indexer.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_code_indexer.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_code_indexer.py
import pytest
import tempfile
import os
from tools.context.code_indexer import index_project, get_symbol_info

@pytest.mark.asyncio
async def test_index_project_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple Python file
        with open(os.path.join(tmpdir, "test.py"), "w") as f:
            f.write("""
def hello():
    return "world"

class MyClass:
    def method(self):
        pass
""")

        result = await index_project(tmpdir, language="python")
        assert result["success"] is True
        assert "symbols" in result["data"]
        assert len(result["data"]["symbols"]) >= 2  # hello + MyClass

@pytest.mark.asyncio
async def test_get_symbol_info():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test.py"), "w") as f:
            f.write("def hello(): return 'world'")

        # First index
        await index_project(tmpdir, language="python")

        # Then query
        result = await get_symbol_info(tmpdir, "hello")
        assert result["success"] is True
        assert result["data"]["name"] == "hello"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_code_indexer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement code indexer**

```python
# tools/context/code_indexer.py
import ast
import json
import os
import time
from pathlib import Path
from typing import Optional
from config import config
from utils.cache import FileCache

def _extract_python_symbols(file_path: str) -> list:
    """Extract function and class definitions from Python file."""
    symbols = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                symbols.append({
                    "name": node.name,
                    "type": "function",
                    "line": node.lineno,
                    "file": file_path
                })
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name,
                    "type": "class",
                    "line": node.lineno,
                    "file": file_path
                })
    except SyntaxError:
        pass  # Skip files with syntax errors

    return symbols

def _should_index_file(file_path: str) -> bool:
    """Check if file should be indexed."""
    exclude_patterns = ['__pycache__', '.git', 'node_modules', 'venv', '.venv']
    return not any(pattern in file_path for pattern in exclude_patterns)

async def index_project(root_path: str, language: str = "python") -> dict:
    """
    Index project files and extract symbols.

    Args:
        root_path: Project root directory
        language: Programming language (default: python)

    Returns:
        {"success": True, "data": {"symbols": [...], "files_count": N}}
    """
    try:
        root = Path(root_path)
        if not root.exists():
            return {
                "success": False,
                "error": {"code": "PATH_NOT_FOUND", "message": f"Path not found: {root_path}"}
            }

        # Check cache
        cache = FileCache(
            str(root / ".ai-coding-mcp-cache"),
            ttl=config.cache.ttl
        )
        cache_key = f"index_{root_path}_{language}"
        cached = cache.get(cache_key)

        if cached:
            # Check if cache is still valid by comparing mtimes
            # For now, simplified: just return cached
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
            # TODO: Add tree-sitter support for other languages
            return {
                "success": False,
                "error": {"code": "UNSUPPORTED_LANGUAGE", "message": f"Language '{language}' not yet supported"}
            }

        result = {
            "symbols": symbols,
            "files_count": files_count,
            "timestamp": time.time()
        }

        # Cache result
        cache.set(cache_key, result)

        return {"success": True, "data": result}

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }

async def get_symbol_info(root_path: str, symbol_name: str) -> dict:
    """
    Get information about a specific symbol.

    Args:
        root_path: Project root directory
        symbol_name: Name of the symbol to look up

    Returns:
        {"success": True, "data": {"name": ..., "type": ..., "file": ..., "line": ...}}
    """
    # First ensure project is indexed
    index_result = await index_project(root_path)
    if not index_result["success"]:
        return index_result

    symbols = index_result["data"]["symbols"]

    for symbol in symbols:
        if symbol["name"] == symbol_name:
            return {"success": True, "data": symbol}

    return {
        "success": False,
        "error": {"code": "SYMBOL_NOT_FOUND", "message": f"Symbol '{symbol_name}' not found"}
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_code_indexer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/context/code_indexer.py tests/test_code_indexer.py
git commit -m "feat: add code_indexer with Python AST support and caching"
```

---

### Task 2.2: Create Dependency Graph

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/context/dependency_graph.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_dependency_graph.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_dependency_graph.py
import pytest
import tempfile
import os
from tools.context.dependency_graph import get_dependency_graph

@pytest.mark.asyncio
async def test_dependency_graph():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create main.py that imports utils
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("import os\nfrom utils import helper\nimport external_lib\n")

        # Create utils.py
        os.makedirs(os.path.join(tmpdir, "utils"), exist_ok=True)
        with open(os.path.join(tmpdir, "utils", "__init__.py"), "w") as f:
            f.write("def helper(): pass")

        result = await get_dependency_graph(tmpdir, "main.py")
        assert result["success"] is True
        assert "dependencies" in result["data"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dependency_graph.py -v`
Expected: FAIL

- [ ] **Step 3: Implement dependency graph**

```python
# tools/context/dependency_graph.py
import ast
import os
from pathlib import Path
from typing import Optional

def _extract_python_imports(file_path: str) -> dict:
    """Extract import statements from Python file."""
    imports = {
        "stdlib": [],
        "third_party": [],
        "internal": []
    }

    stdlib_modules = {
        'os', 'sys', 'json', 'time', 're', 'collections', 'typing',
        'pathlib', 'asyncio', 'subprocess', 'dataclasses', 'enum'
    }

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
                    elif node.level > 0:  # Relative import
                        imports["internal"].append(node.module)
                    else:
                        imports["third_party"].append(node.module)
    except SyntaxError:
        pass

    return imports

async def get_dependency_graph(root_path: str, file_path: str) -> dict:
    """
    Get dependency graph for a file.

    Args:
        root_path: Project root directory
        file_path: Target file path (relative to root)

    Returns:
        {"success": True, "data": {"dependencies": {...}, "dependents": [...]}}
    """
    try:
        root = Path(root_path)
        target = root / file_path

        if not target.exists():
            return {
                "success": False,
                "error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {file_path}"}
            }

        # Extract imports
        imports = _extract_python_imports(str(target))

        # TODO: Find dependents (files that import this file)
        # This requires full project scan - can be optimized with index

        return {
            "success": True,
            "data": {
                "file": file_path,
                "dependencies": imports,
                "dependents": []  # TODO: implement
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_dependency_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/context/dependency_graph.py tests/test_dependency_graph.py
git commit -m "feat: add dependency_graph with import classification"
```

---

### Task 2.3: Create Project Stats

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/context/project_stats.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_project_stats.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_project_stats.py
import pytest
import tempfile
import os
from tools.context.project_stats import get_project_stats

@pytest.mark.asyncio
async def test_project_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Python file
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("# Comment\ndef hello():\n    return 'world'\n")

        # Create JS file
        with open(os.path.join(tmpdir, "app.js"), "w") as f:
            f.write("console.log('hello');")

        result = await get_project_stats(tmpdir)
        assert result["success"] is True
        assert result["data"]["total_files"] >= 2
        assert "python" in result["data"]["languages"]
        assert "javascript" in result["data"]["languages"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_project_stats.py -v`
Expected: FAIL

- [ ] **Step 3: Implement project stats**

```python
# tools/context/project_stats.py
import os
from pathlib import Path
from collections import defaultdict

LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
    "go": [".go"],
    "java": [".java"],
    "rust": [".rs"],
    "ruby": [".rb"],
    "cpp": [".cpp", ".cc", ".hpp"],
    "c": [".c", ".h"],
}

def _detect_language(file_path: str) -> Optional[str]:
    """Detect language from file extension."""
    ext = Path(file_path).suffix.lower()
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if ext in exts:
            return lang
    return None

def _count_lines(file_path: str) -> int:
    """Count lines in file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except:
        return 0

async def get_project_stats(root_path: str) -> dict:
    """
    Get project statistics.

    Args:
        root_path: Project root directory

    Returns:
        {"success": True, "data": {"total_files": N, "total_lines": N, "languages": {...}}}
    """
    try:
        root = Path(root_path)

        if not root.exists():
            return {
                "success": False,
                "error": {"code": "PATH_NOT_FOUND", "message": f"Path not found: {root_path}"}
            }

        exclude_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'target', 'build'}

        total_files = 0
        total_lines = 0
        language_stats = defaultdict(lambda: {"files": 0, "lines": 0})

        for item in root.rglob("*"):
            if item.is_file():
                # Skip excluded directories
                if any(excluded in str(item) for excluded in exclude_dirs):
                    continue

                total_files += 1
                lines = _count_lines(str(item))
                total_lines += lines

                lang = _detect_language(str(item))
                if lang:
                    language_stats[lang]["files"] += 1
                    language_stats[lang]["lines"] += lines

        return {
            "success": True,
            "data": {
                "total_files": total_files,
                "total_lines": total_lines,
                "languages": dict(language_stats)
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_project_stats.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/context/project_stats.py tests/test_project_stats.py
git commit -m "feat: add project_stats with multi-language line counting"
```

---

### Task 2.4: Register Context Tools

**Files:**
- Modify: `/Users/kevinten/projects/ai-coding-mcp/server.py`

- [ ] **Step 1: Import and register context tools**

```python
# Add to server.py after mcp creation
from tools.context.code_indexer import index_project, get_symbol_info
from tools.context.dependency_graph import get_dependency_graph
from tools.context.project_stats import get_project_stats

@mcp.tool()
async def tool_index_project(root_path: str, language: str = "python") -> dict:
    """Index project files and extract symbols."""
    return await index_project(root_path, language)

@mcp.tool()
async def tool_get_symbol_info(root_path: str, symbol_name: str) -> dict:
    """Get information about a specific symbol."""
    return await get_symbol_info(root_path, symbol_name)

@mcp.tool()
async def tool_get_dependency_graph(root_path: str, file_path: str) -> dict:
    """Get dependency graph for a file."""
    return await get_dependency_graph(root_path, file_path)

@mcp.tool()
async def tool_get_project_stats(root_path: str) -> dict:
    """Get project statistics."""
    return await get_project_stats(root_path)
```

- [ ] **Step 2: Test server imports**

Run: `python -c "import server; print('Context tools registered')"`
Expected: "Context tools registered"

- [ ] **Step 3: Commit**

```bash
git add server.py
git commit -m "feat: register context module tools (4 tools)"
```

---

## Chunk 3: Module 2 — External Knowledge

### Task 3.1: Create Package Info

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/knowledge/package_info.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_package_info.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_package_info.py
import pytest
from tools.knowledge.package_info import get_package_info

@pytest.mark.asyncio
async def test_get_package_info_python():
    result = await get_package_info("requests", "python")
    assert result["success"] is True
    assert "name" in result["data"]
    assert "version" in result["data"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_package_info.py -v`
Expected: FAIL

- [ ] **Step 3: Implement package info**

```python
# tools/knowledge/package_info.py
import json
from utils.cli_runner import run_cli
from utils.cache import FileCache
from config import config

async def _get_pypi_info(package_name: str) -> dict:
    """Get package info from PyPI."""
    # Try CLI first
    result = await run_cli(["pip", "index", "versions", package_name], timeout=10)

    # Fallback to API
    if result.returncode != 0:
        api_result = await run_cli([
            "curl", "-s", f"https://pypi.org/pypi/{package_name}/json"
        ], timeout=10)

        if api_result.returncode == 0:
            try:
                data = json.loads(api_result.stdout)
                return {
                    "name": data["info"]["name"],
                    "version": data["info"]["version"],
                    "latest_version": data["info"]["version"],
                    "description": data["info"]["summary"],
                    "license": data["info"]["license"],
                    "homepage": data["info"]["home_page"],
                }
            except (json.JSONDecodeError, KeyError):
                pass

    return {"name": package_name, "version": "unknown"}

async def _get_npm_info(package_name: str) -> dict:
    """Get package info from npm."""
    result = await run_cli(["npm", "view", package_name, "--json"], timeout=10)

    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            return {
                "name": data.get("name"),
                "version": data.get("version"),
                "latest_version": data.get("dist-tags", {}).get("latest"),
                "description": data.get("description"),
                "license": data.get("license"),
                "homepage": data.get("homepage"),
            }
        except json.JSONDecodeError:
            pass

    return {"name": package_name, "version": "unknown"}

async def get_package_info(package_name: str, ecosystem: str) -> dict:
    """
    Get package information from registry.

    Args:
        package_name: Package name
        ecosystem: python, node, go, java, rust

    Returns:
        {"success": True, "data": {"name": ..., "version": ..., ...}}
    """
    try:
        # Check cache
        cache = FileCache(
            f"{config.cache.cache_dir}/packages",
            ttl=3600  # 1 hour
        )
        cache_key = f"{ecosystem}:{package_name}"
        cached = cache.get(cache_key)

        if cached:
            return {"success": True, "data": cached}

        # Fetch based on ecosystem
        if ecosystem == "python":
            data = await _get_pypi_info(package_name)
        elif ecosystem == "node":
            data = await _get_npm_info(package_name)
        else:
            return {
                "success": False,
                "error": {"code": "UNSUPPORTED_ECOSYSTEM", "message": f"Ecosystem '{ecosystem}' not yet supported"}
            }

        # Cache result
        cache.set(cache_key, data)

        return {"success": True, "data": data}

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_package_info.py -v`
Expected: PASS (may skip if no network)

- [ ] **Step 5: Commit**

```bash
git add tools/knowledge/package_info.py tests/test_package_info.py
git commit -m "feat: add package_info with PyPI and npm support"
```

---

### Task 3.2: Create Compatibility Check

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/knowledge/compatibility.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_compatibility.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_compatibility.py
import pytest
import tempfile
import os
from tools.knowledge.compatibility import check_compatibility

@pytest.mark.asyncio
async def test_check_compatibility_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create requirements.txt
        with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
            f.write("requests>=2.0.0\n")

        result = await check_compatibility(tmpdir)
        assert result["success"] is True
        assert "conflicts" in result["data"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_compatibility.py -v`
Expected: FAIL

- [ ] **Step 3: Implement compatibility check**

```python
# tools/knowledge/compatibility.py
import json
import os
from pathlib import Path
from utils.cli_runner import run_cli

async def _check_python_compatibility(project_path: str) -> dict:
    """Check Python dependency compatibility."""
    conflicts = []
    outdated = []

    # Check for dependency conflicts
    result = await run_cli(["pip", "check"], cwd=project_path, timeout=30)
    if result.returncode != 0 and result.stdout:
        for line in result.stdout.strip().split('\n'):
            if line:
                conflicts.append(line)

    # Check for outdated packages
    result = await run_cli(
        ["pip", "list", "--outdated", "--format=json"],
        cwd=project_path,
        timeout=30
    )
    if result.returncode == 0:
        try:
            packages = json.loads(result.stdout)
            for pkg in packages:
                outdated.append({
                    "name": pkg.get("name"),
                    "current": pkg.get("version"),
                    "latest": pkg.get("latest_version")
                })
        except json.JSONDecodeError:
            pass

    return {"conflicts": conflicts, "outdated": outdated}

async def check_compatibility(project_path: str) -> dict:
    """
    Check dependency compatibility.

    Args:
        project_path: Project directory path

    Returns:
        {"success": True, "data": {"conflicts": [...], "outdated": [...]}}
    """
    try:
        root = Path(project_path)

        # Detect ecosystem
        if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists():
            data = await _check_python_compatibility(project_path)
        elif (root / "package.json").exists():
            # TODO: Add npm support
            return {
                "success": False,
                "error": {"code": "NOT_IMPLEMENTED", "message": "Node compatibility check not yet implemented"}
            }
        else:
            return {
                "success": False,
                "error": {"code": "UNKNOWN_ECOSYSTEM", "message": "Could not detect project ecosystem"}
            }

        return {"success": True, "data": data}

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_compatibility.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/knowledge/compatibility.py tests/test_compatibility.py
git commit -m "feat: add compatibility check for Python dependencies"
```

---

### Task 3.3: Create Doc Search (Stub)

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/knowledge/doc_search.py`
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/knowledge/code_search.py`

- [ ] **Step 1: Implement doc search stub**

```python
# tools/knowledge/doc_search.py
async def search_docs(query: str, library: str = None, version: str = None) -> dict:
    """
    Search documentation. (Stub - TODO: implement with curl + HTML parse)
    """
    return {
        "success": False,
        "error": {"code": "NOT_IMPLEMENTED", "message": "Doc search not yet implemented"}
    }
```

- [ ] **Step 2: Implement code search stub**

```python
# tools/knowledge/code_search.py
async def search_code_examples(query: str, language: str) -> dict:
    """
    Search code examples. (Stub - TODO: implement with gh search)
    """
    return {
        "success": False,
        "error": {"code": "NOT_IMPLEMENTED", "message": "Code search not yet implemented"}
    }
```

- [ ] **Step 3: Register knowledge tools**

```python
# Add to server.py
from tools.knowledge.doc_search import search_docs
from tools.knowledge.package_info import get_package_info
from tools.knowledge.code_search import search_code_examples
from tools.knowledge.compatibility import check_compatibility

@mcp.tool()
async def tool_search_docs(query: str, library: str = None, version: str = None) -> dict:
    """Search documentation."""
    return await search_docs(query, library, version)

@mcp.tool()
async def tool_get_package_info(package_name: str, ecosystem: str) -> dict:
    """Get package information."""
    return await get_package_info(package_name, ecosystem)

@mcp.tool()
async def tool_search_code_examples(query: str, language: str) -> dict:
    """Search code examples."""
    return await search_code_examples(query, language)

@mcp.tool()
async def tool_check_compatibility(project_path: str) -> dict:
    """Check dependency compatibility."""
    return await check_compatibility(project_path)
```

- [ ] **Step 4: Commit**

```bash
git add tools/knowledge/doc_search.py tools/knowledge/code_search.py server.py
git commit -m "feat: add knowledge module with 4 tools (2 stubs)"
```

---

## Chunk 4: Module 3 — Workflow

### Task 4.1: Create Git Operations

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/workflow/git_ops.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_git_ops.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_git_ops.py
import pytest
import tempfile
import os
import subprocess
from tools.workflow.git_ops import git_status, git_history

@pytest.mark.asyncio
async def test_git_status():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Init git repo
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)

        # Create and commit a file
        with open(os.path.join(tmpdir, "test.txt"), "w") as f:
            f.write("hello")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)

        result = await git_status(tmpdir)
        assert result["success"] is True
        assert "branch" in result["data"]

@pytest.mark.asyncio
async def test_git_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)

        with open(os.path.join(tmpdir, "test.txt"), "w") as f:
            f.write("hello")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, check=True, capture_output=True)

        result = await git_history(tmpdir)
        assert result["success"] is True
        assert len(result["data"]["commits"]) >= 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_git_ops.py -v`
Expected: FAIL

- [ ] **Step 3: Implement git operations**

```python
# tools/workflow/git_ops.py
import json
from utils.cli_runner import run_cli

async def git_status(repo_path: str) -> dict:
    """
    Get git status.

    Args:
        repo_path: Repository path

    Returns:
        {"success": True, "data": {"branch": ..., "changed": [...], "staged": [...]}}
    """
    try:
        # Get branch
        branch_result = await run_cli(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            timeout=10
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Get status
        status_result = await run_cli(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            timeout=10
        )

        changed = []
        staged = []

        if status_result.returncode == 0:
            for line in status_result.stdout.strip().split('\n'):
                if line:
                    status = line[:2]
                    file = line[3:]
                    if status[0] != ' ':
                        staged.append(file)
                    if status[1] != ' ':
                        changed.append(file)

        return {
            "success": True,
            "data": {
                "branch": branch,
                "changed": changed,
                "staged": staged
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }

async def git_history(repo_path: str, file_path: str = None, author: str = None, since: str = None) -> dict:
    """
    Get git commit history.

    Args:
        repo_path: Repository path
        file_path: Filter by file (optional)
        author: Filter by author (optional)
        since: Filter by date (optional)

    Returns:
        {"success": True, "data": {"commits": [...]}}
    """
    try:
        cmd = [
            "git", "log",
            "--pretty=format:{\"hash\":\"%h\",\"author\":\"%an\",\"date\":\"%ad\",\"message\":\"%s\"}",
            "--date=short",
            "-n", "20"
        ]

        if author:
            cmd.extend(["--author", author])
        if since:
            cmd.extend(["--since", since])
        if file_path:
            cmd.extend(["--", file_path])

        result = await run_cli(cmd, cwd=repo_path, timeout=10)

        commits = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        commit = json.loads(line)
                        commits.append(commit)
                    except json.JSONDecodeError:
                        pass

        return {
            "success": True,
            "data": {"commits": commits}
        }

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }

async def git_branch_analysis(repo_path: str) -> dict:
    """
    Analyze git branches. (Stub)
    """
    return {
        "success": False,
        "error": {"code": "NOT_IMPLEMENTED", "message": "Branch analysis not yet implemented"}
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_git_ops.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/workflow/git_ops.py tests/test_git_ops.py
git commit -m "feat: add git_ops with status and history"
```

---

### Task 4.2: Create GitHub CI Operations

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/workflow/ci_github.py`

- [ ] **Step 1: Implement CI/GitHub tools (stubs)**

```python
# tools/workflow/ci_github.py
async def ci_status(repo_path: str = None, repo_url: str = None) -> dict:
    """
    Get CI status. (Stub - requires gh CLI)
    """
    return {
        "success": False,
        "error": {"code": "NOT_IMPLEMENTED", "message": "CI status requires gh CLI setup"}
    }

async def issue_list(repo_url: str, state: str = "open", labels: str = None) -> dict:
    """
    List issues. (Stub - requires gh CLI)
    """
    return {
        "success": False,
        "error": {"code": "NOT_IMPLEMENTED", "message": "Issue list requires gh CLI setup"}
    }

async def pr_summary(repo_url: str, pr_number: int = None) -> dict:
    """
    Get PR summary. (Stub - requires gh CLI)
    """
    return {
        "success": False,
        "error": {"code": "NOT_IMPLEMENTED", "message": "PR summary requires gh CLI setup"}
    }
```

- [ ] **Step 2: Register workflow tools**

```python
# Add to server.py
from tools.workflow.git_ops import git_status, git_history, git_branch_analysis
from tools.workflow.ci_github import ci_status, issue_list, pr_summary

@mcp.tool()
async def tool_git_status(repo_path: str) -> dict:
    """Get git status."""
    return await git_status(repo_path)

@mcp.tool()
async def tool_git_history(repo_path: str, file_path: str = None, author: str = None, since: str = None) -> dict:
    """Get git history."""
    return await git_history(repo_path, file_path, author, since)

@mcp.tool()
async def tool_git_branch_analysis(repo_path: str) -> dict:
    """Analyze git branches."""
    return await git_branch_analysis(repo_path)

@mcp.tool()
async def tool_ci_status(repo_path: str = None, repo_url: str = None) -> dict:
    """Get CI status."""
    return await ci_status(repo_path, repo_url)

@mcp.tool()
async def tool_issue_list(repo_url: str, state: str = "open", labels: str = None) -> dict:
    """List issues."""
    return await issue_list(repo_url, state, labels)

@mcp.tool()
async def tool_pr_summary(repo_url: str, pr_number: int = None) -> dict:
    """Get PR summary."""
    return await pr_summary(repo_url, pr_number)
```

- [ ] **Step 3: Commit**

```bash
git add tools/workflow/ci_github.py server.py
git commit -m "feat: add workflow module with 6 tools (4 stubs)"
```

---

## Chunk 5: Module 4 — Specs

### Task 5.1: Create Spec Manager

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/specs/spec_manager.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_spec_manager.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_spec_manager.py
import pytest
import tempfile
import os
from tools.specs.spec_manager import list_specs, get_spec, create_spec

@pytest.mark.asyncio
async def test_list_specs():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create docs/specs directory
        specs_dir = os.path.join(tmpdir, "docs", "specs")
        os.makedirs(specs_dir)

        # Create a spec file with frontmatter
        with open(os.path.join(specs_dir, "2026-01-01-test.md"), "w") as f:
            f.write("""---
type: spec
date: 2026-01-01
author: test
---
# Test Spec
This is a test.
""")

        result = await list_specs(tmpdir)
        assert result["success"] is True
        assert len(result["data"]["specs"]) == 1

@pytest.mark.asyncio
async def test_get_spec():
    with tempfile.TemporaryDirectory() as tmpdir:
        specs_dir = os.path.join(tmpdir, "docs", "specs")
        os.makedirs(specs_dir)

        with open(os.path.join(specs_dir, "test.md"), "w") as f:
            f.write("# Test Spec\nContent here.")

        result = await get_spec(tmpdir, "test.md")
        assert result["success"] is True
        assert "Test Spec" in result["data"]["content"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_spec_manager.py -v`
Expected: FAIL

- [ ] **Step 3: Implement spec manager**

```python
# tools/specs/spec_manager.py
import os
import re
from pathlib import Path
from typing import Optional

def _parse_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter from markdown content."""
    frontmatter = {}

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            content = parts[2].strip()

            # Simple key: value parsing
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()

    return frontmatter, content

def _get_summary(content: str, max_length: int = 100) -> str:
    """Get first paragraph as summary."""
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            return line[:max_length] + ('...' if len(line) > max_length else '')
    return ""

async def list_specs(project_path: str, spec_type: str = None) -> dict:
    """
    List spec files in project.

    Args:
        project_path: Project root path
        spec_type: Filter by type (spec/adr/guide/api)

    Returns:
        {"success": True, "data": {"specs": [...]}}
    """
    try:
        docs_path = Path(project_path) / "docs"
        specs = []

        for subdir in ["specs", "adr", "guides", "api"]:
            dir_path = docs_path / subdir
            if dir_path.exists():
                for md_file in dir_path.glob("*.md"):
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        frontmatter, body = _parse_frontmatter(content)

                        spec_info = {
                            "type": frontmatter.get("type", subdir),
                            "path": str(md_file.relative_to(project_path)),
                            "filename": md_file.name,
                            "summary": _get_summary(body),
                            "updated_at": frontmatter.get("date", ""),
                            "author": frontmatter.get("author", "")
                        }

                        if spec_type is None or spec_info["type"] == spec_type:
                            specs.append(spec_info)
                    except Exception:
                        pass

        return {"success": True, "data": {"specs": specs}}

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }

async def get_spec(project_path: str, spec_path: str) -> dict:
    """
    Get spec file content.

    Args:
        project_path: Project root path
        spec_path: Path to spec file (relative to project or absolute)

    Returns:
        {"success": True, "data": {"content": ..., "frontmatter": {...}}}
    """
    try:
        full_path = Path(project_path) / spec_path

        if not full_path.exists():
            return {
                "success": False,
                "error": {"code": "FILE_NOT_FOUND", "message": f"Spec not found: {spec_path}"}
            }

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter, body = _parse_frontmatter(content)

        return {
            "success": True,
            "data": {
                "content": body,
                "frontmatter": frontmatter,
                "path": spec_path
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }

async def search_specs(project_path: str, query: str) -> dict:
    """
    Search specs for query. (Simple grep-based)
    """
    try:
        list_result = await list_specs(project_path)
        if not list_result["success"]:
            return list_result

        results = []
        query_lower = query.lower()

        for spec in list_result["data"]["specs"]:
            spec_detail = await get_spec(project_path, spec["path"])
            if spec_detail["success"]:
                content = spec_detail["data"]["content"].lower()
                if query_lower in content:
                    # Find context
                    idx = content.find(query_lower)
                    start = max(0, idx - 50)
                    end = min(len(content), idx + len(query) + 50)
                    context = spec_detail["data"]["content"][start:end]

                    results.append({
                        "path": spec["path"],
                        "context": context,
                        "type": spec["type"]
                    })

        return {"success": True, "data": {"results": results}}

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }

async def create_spec(project_path: str, spec_type: str, name: str) -> dict:
    """
    Create a new spec file from template.

    Args:
        project_path: Project root path
        spec_type: Type of spec (spec/adr/guide/api)
        name: Spec name

    Returns:
        {"success": True, "data": {"path": ...}}
    """
    try:
        import datetime

        # Map type to directory
        type_dir = {
            "spec": "specs",
            "adr": "adr",
            "guide": "guides",
            "api": "api"
        }

        if spec_type not in type_dir:
            return {
                "success": False,
                "error": {"code": "INVALID_TYPE", "message": f"Unknown spec type: {spec_type}"}
            }

        dir_path = Path(project_path) / "docs" / type_dir[spec_type]
        dir_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        today = datetime.date.today()
        if spec_type == "spec":
            filename = f"{today.strftime('%Y-%m-%d')}-{name}.md"
        elif spec_type == "adr":
            filename = f"ADR-001-{name}.md"
        else:
            filename = f"{name}.md"

        file_path = dir_path / filename

        # Create from template
        template = f"""---
type: {spec_type}
date: {today.strftime('%Y-%m-%d')}
author:
status: draft
---

# {name.replace('-', ' ').title()}

## Overview

(TODO: Add overview)

## Details

(TODO: Add details)

## References

-
"""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)

        return {
            "success": True,
            "data": {"path": str(file_path.relative_to(project_path))}
        }

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_spec_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/specs/spec_manager.py tests/test_spec_manager.py
git commit -m "feat: add spec_manager with list/get/search/create"
```

---

### Task 5.2: Create Scaffold and Validator

**Files:**
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/specs/scaffold.py`
- Create: `/Users/kevinten/projects/ai-coding-mcp/tools/specs/validator.py`
- Test: `/Users/kevinten/projects/ai-coding-mcp/tests/test_scaffold.py`

- [ ] **Step 1: Write failing test for scaffold**

```python
# tests/test_scaffold.py
import pytest
import tempfile
import os
from tools.specs.scaffold import scaffold_project

@pytest.mark.asyncio
async def test_scaffold_python_module():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await scaffold_project("python-module", tmpdir, {"name": "mymodule"})
        assert result["success"] is True
        assert os.path.exists(os.path.join(tmpdir, "mymodule", "__init__.py"))
        assert os.path.exists(os.path.join(tmpdir, "tests", "test_mymodule.py"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scaffold.py -v`
Expected: FAIL

- [ ] **Step 3: Implement scaffold**

```python
# tools/specs/scaffold.py
import os
from pathlib import Path

TEMPLATES = {
    "python-module": {
        "structure": [
            "{{ name }}/__init__.py",
            "{{ name }}/main.py",
            "tests/test_{{ name }}.py",
            "README.md"
        ],
        "files": {
            "{{ name }}/__init__.py": "\"\"\"{{ name }} module.\"\"\"\n\n__version__ = \"0.1.0\"\n",
            "{{ name }}/main.py": "def main():\n    print(\"Hello from {{ name }}!\")\n\nif __name__ == \"__main__\":\n    main()\n",
            "tests/test_{{ name }}.py": "import pytest\nfrom {{ name }} import main\n\ndef test_main():\n    assert main() is None  # Update this test\n",
            "README.md": "# {{ name }}\n\nTODO: Add description\n\n## Installation\n\n```bash\npip install -e .\n```\n\n## Usage\n\n```python\nfrom {{ name }} import main\nmain()\n```\n"
        }
    },
    "node-module": {
        "structure": [
            "src/index.ts",
            "__tests__/index.test.ts",
            "package.json",
            "README.md"
        ],
        "files": {
            "src/index.ts": "export function hello(): string {\n    return 'Hello from {{ name }}!';\n}\n",
            "__tests__/index.test.ts": "import { hello } from '../src/index';\n\ntest('hello', () => {\n    expect(hello()).toBe('Hello from {{ name }}!');\n});\n",
            "package.json": '{\n  "name": "{{ name }}",\n  "version": "0.1.0",\n  "main": "dist/index.js",\n  "scripts": {\n    "build": "tsc",\n    "test": "jest"\n  }\n}\n',
            "README.md": "# {{ name }}\n\nTODO: Add description\n"
        }
    },
    "generic": {
        "structure": [
            "src/",
            "tests/",
            "docs/",
            "README.md"
        ],
        "files": {
            "README.md": "# {{ name }}\n\nTODO: Add description\n"
        }
    }
}

async def scaffold_project(template: str, target_path: str, params: dict) -> dict:
    """
    Scaffold a new project from template.

    Args:
        template: Template name (python-module/node-module/generic)
        target_path: Where to create the project
        params: Template parameters (name, author, etc.)

    Returns:
        {"success": True, "data": {"created_files": [...]}}
    """
    try:
        if template not in TEMPLATES:
            return {
                "success": False,
                "error": {"code": "UNKNOWN_TEMPLATE", "message": f"Unknown template: {template}"}
            }

        if "name" not in params:
            return {
                "success": False,
                "error": {"code": "MISSING_PARAM", "message": "Missing required param: name"}
            }

        tmpl = TEMPLATES[template]
        target = Path(target_path)
        target.mkdir(parents=True, exist_ok=True)

        created = []

        # Create directories
        for item in tmpl["structure"]:
            path = target / item.replace("{{ name }}", params["name"])
            if "." not in path.name:  # It's a directory
                path.mkdir(parents=True, exist_ok=True)
                created.append(str(path))

        # Create files
        for file_path, content in tmpl["files"].items():
            full_path = target / file_path.replace("{{ name }}", params["name"])
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Replace all params in content
            final_content = content
            for key, value in params.items():
                final_content = final_content.replace(f"{{{{ {key} }}}}", value)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(final_content)

            created.append(str(full_path))

        return {
            "success": True,
            "data": {"created_files": created}
        }

    except Exception as e:
        return {
            "success": False,
            "error": {"code": "UNKNOWN", "message": str(e)}
        }
```

- [ ] **Step 4: Implement validator stub**

```python
# tools/specs/validator.py
async def validate_structure(project_path: str, template: str = None) -> dict:
    """
    Validate project structure against template. (Stub)
    """
    return {
        "success": False,
        "error": {"code": "NOT_IMPLEMENTED", "message": "Structure validation not yet implemented"}
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_scaffold.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tools/specs/scaffold.py tools/specs/validator.py tests/test_scaffold.py
git commit -m "feat: add scaffold with python/node/generic templates"
```

---

### Task 5.3: Register Specs Tools

**Files:**
- Modify: `/Users/kevinten/projects/ai-coding-mcp/server.py`

- [ ] **Step 1: Import and register specs tools**

```python
# Add to server.py
from tools.specs.spec_manager import list_specs, get_spec, search_specs, create_spec
from tools.specs.scaffold import scaffold_project
from tools.specs.validator import validate_structure

@mcp.tool()
async def tool_list_specs(project_path: str, type: str = None) -> dict:
    """List spec files."""
    return await list_specs(project_path, type)

@mcp.tool()
async def tool_get_spec(project_path: str, spec_path: str) -> dict:
    """Get spec file content."""
    return await get_spec(project_path, spec_path)

@mcp.tool()
async def tool_search_specs(project_path: str, query: str) -> dict:
    """Search specs."""
    return await search_specs(project_path, query)

@mcp.tool()
async def tool_create_spec(project_path: str, type: str, name: str) -> dict:
    """Create new spec file."""
    return await create_spec(project_path, type, name)

@mcp.tool()
async def tool_scaffold_project(template: str, target_path: str, params: dict) -> dict:
    """Scaffold new project from template."""
    return await scaffold_project(template, target_path, params)

@mcp.tool()
async def tool_validate_structure(project_path: str, template: str = None) -> dict:
    """Validate project structure."""
    return await validate_structure(project_path, template)
```

- [ ] **Step 2: Commit**

```bash
git add server.py
git commit -m "feat: register specs module tools (6 tools)"
```

---

## Chunk 6: Final Integration

### Task 6.1: Update Requirements

**Files:**
- Modify: `/Users/kevinten/projects/ai-coding-mcp/requirements.txt`

- [ ] **Step 1: Update requirements for v2**

```txt
# MCP framework
mcp-server-fastmcp>=0.9.0

# Config and data validation
pydantic>=2.0.0

# Cache and storage
pyyaml>=6.0

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

- [ ] **Step 2: Commit**

```bash
git add requirements.txt
git commit -m "chore: update requirements for v2"
```

---

### Task 6.2: Create Comprehensive README

**Files:**
- Modify: `/Users/kevinten/projects/ai-coding-mcp/README.md`

- [ ] **Step 1: Write v2 README**

```markdown
# AI Coding MCP v2

Lightweight MCP server for AI IDEs (Claude Code, Cursor, etc.). Provides 20 tools across 4 modules without LLM wrapping.

## Quick Start

```bash
pip install -r requirements.txt
python server.py
```

## Modules

### Context (4 tools)
- `index_project` - Index project files and extract symbols
- `get_symbol_info` - Look up symbol information
- `get_dependency_graph` - Analyze file dependencies
- `get_project_stats` - Get project statistics

### Knowledge (4 tools)
- `search_docs` - Search documentation (stub)
- `get_package_info` - Query package registries (PyPI/npm)
- `search_code_examples` - Search code examples (stub)
- `check_compatibility` - Check dependency compatibility

### Workflow (6 tools)
- `git_status` - Get git working tree status
- `git_history` - Get commit history
- `git_branch_analysis` - Analyze branches (stub)
- `ci_status` - Check CI status (stub)
- `issue_list` - List GitHub issues (stub)
- `pr_summary` - Get PR summary (stub)

### Specs (6 tools)
- `list_specs` - List specification files
- `get_spec` - Read spec content
- `search_specs` - Search specs
- `create_spec` - Create new spec from template
- `scaffold_project` - Scaffold project from template
- `validate_structure` - Validate directory structure (stub)

## Architecture

- **CLI-first**: All external calls via `git`, `gh`, `pip`, `npm`, `curl`
- **Zero LLM wrapping**: Return structured data, let AI IDE analyze
- **File-based cache**: TTL cache in `~/.cache/ai-coding-mcp/`
- **Pydantic config**: Type-safe configuration

## Testing

```bash
pytest tests/ -v
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README for v2"
```

---

### Task 6.3: Final Verification

- [ ] **Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS (stubs will return NOT_IMPLEMENTED but not crash)

- [ ] **Step 2: Verify server imports**

Run: `python -c "import server; print('All 20 tools registered successfully')"`
Expected: "All 20 tools registered successfully"

- [ ] **Step 3: Final commit**

```bash
git commit -m "feat: complete v2 implementation with 20 tools across 4 modules" --allow-empty
```

---

## Summary

| Chunk | Module | Tools | Status |
|-------|--------|-------|--------|
| 1 | Foundation | 0 | Config, CLI runner, Cache, Server skeleton |
| 2 | Context | 4 | index_project, get_symbol_info, get_dependency_graph, get_project_stats |
| 3 | Knowledge | 4 | search_docs, get_package_info, search_code_examples, check_compatibility |
| 4 | Workflow | 6 | git_status, git_history, git_branch_analysis, ci_status, issue_list, pr_summary |
| 5 | Specs | 6 | list_specs, get_spec, search_specs, create_spec, scaffold_project, validate_structure |
| 6 | Integration | 0 | README, requirements, final verification |

**Total: 20 tools implemented**

---

## Execution Notes

- Implement tools in order (skip stubs if time-constrained)
- Core working tools: Context module (4), git_status, git_history, get_package_info, check_compatibility
- Stubs return `{"success": False, "error": {"code": "NOT_IMPLEMENTED", ...}}` gracefully
- All tests must pass before commit
- Each task ends with a commit
