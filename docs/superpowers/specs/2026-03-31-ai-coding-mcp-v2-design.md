# AI Coding MCP v2 Design Spec

**Date:** 2026-03-31
**Status:** Approved
**Author:** kevinten

---

## 1. Overview

### 1.1 What

A lightweight MCP server designed for AI IDEs (Claude Code, Cursor, etc.) that provides structured data and deterministic operations the AI cannot do natively. No LLM wrapping — all tools return raw data for the AI to analyze.

### 1.2 Why

The existing v1 architecture wraps LLM calls inside MCP tools, which is redundant when the consumer is already an LLM-powered IDE. This redesign pivots to providing capabilities the AI IDE lacks: project context indexing, external package/doc queries, Git/CI workflow data, and project spec management.

### 1.3 Design Principles

1. **Data, not judgment** — Return structured data; let the AI IDE do analysis
2. **CLI-first** — Backend uses `git`, `gh`, `pip`, `npm`, `go`, `cargo`, `curl` — zero third-party MCP dependencies
3. **Multi-language** — Route via `language`/`ecosystem` parameter to different CLI backends; priority: Python, Node, Go, Java, Rust
4. **Read-mostly** — Only `create_spec` and `scaffold_project` write to disk; everything else is read-only

---

## 2. Architecture

### 2.1 Directory Structure

```
ai-coding-mcp/
├── server.py                    # FastMCP entry, tool registration
├── config.py                    # Pydantic config (simplified from v1)
├── tools/
│   ├── context/                 # Module 1: Project context
│   │   ├── code_indexer.py      #   AST/tree-sitter indexing
│   │   ├── dependency_graph.py  #   Import analysis, dependency graph
│   │   └── project_stats.py    #   Language distribution, LOC, complexity
│   ├── knowledge/               # Module 2: External knowledge
│   │   ├── doc_search.py        #   Doc site search (curl + HTML parse)
│   │   ├── package_info.py      #   Multi-ecosystem package info
│   │   ├── code_search.py       #   GitHub code search (gh CLI)
│   │   └── compatibility.py     #   Dependency conflict detection
│   ├── workflow/                 # Module 3: Dev workflow
│   │   ├── git_ops.py           #   Git status/history/branch (read-only)
│   │   └── ci_github.py         #   CI status + Issue/PR queries (gh CLI)
│   └── specs/                   # Module 4: Spec management
│       ├── spec_manager.py      #   Spec file index/query/create
│       ├── scaffold.py          #   Directory scaffolding (multi-lang templates)
│       └── validator.py         #   Structure compliance check
├── utils/
│   ├── security.py              # Path validation (reused from v1, adapted)
│   ├── cli_runner.py            # Unified CLI executor (subprocess wrapper)
│   ├── cache.py                 # File-based cache with TTL
│   └── parsers.py               # Multi-language AST parser router
├── templates/                   # Built-in templates
│   ├── specs/                   #   Spec file templates (spec/adr/guide)
│   └── projects/                #   Project scaffold templates
├── tests/
│   ├── test_context/
│   ├── test_knowledge/
│   ├── test_workflow/
│   └── test_specs/
├── requirements.txt
└── README.md
```

### 2.2 Key Dependency: cli_runner

All external CLI calls go through a unified `cli_runner.py`:

```python
async def run_cli(command: list[str], cwd: str = None, timeout: int = 30) -> CLIResult:
    """
    Execute CLI command with timeout, error handling, and output parsing.
    Returns CLIResult(returncode, stdout, stderr, execution_time).
    """
```

This ensures consistent timeout handling, error reporting, and security validation across all tools.

### 2.3 Error Response Convention

All tools return a unified structure on failure:

```python
{
    "success": False,
    "error": {
        "code": "CLI_TIMEOUT" | "CLI_NOT_FOUND" | "PARSE_ERROR" | "PATH_DENIED" | "UNKNOWN",
        "message": "Human-readable error description",
        "command": "The CLI command that failed (if applicable)",
        "suggestion": "Actionable fix suggestion"
    }
}
```

On success, tools return `{"success": True, "data": {...}}` with tool-specific data.

### 2.4 Caching Strategy

Cache lives in `utils/cache.py` — a simple file-based cache keyed by content hash:

- **Project index cache**: Local JSON at `.ai-coding-mcp-cache/index.json` in the project root. Invalidated by file mtime comparison.
- **Package info cache**: Per-package JSON at `~/.cache/ai-coding-mcp/packages/`. TTL: 1 hour.
- **Doc search cache**: Per-query JSON at `~/.cache/ai-coding-mcp/docs/`. TTL: 24 hours.

Cache module added to directory structure under `utils/cache.py`.

### 2.5 Reuse from v1

| Component | Decision | Reason |
|-----------|----------|--------|
| `config.py` | Simplify & keep | Remove AIConfig/LLM tool configs, keep Server/Security/Logging/Cache |
| `utils/security.py` | Reuse with adaptation | Keep path validation + rate limiter; strip `validate_content` (XSS irrelevant for CLI output); relax `validate_url` for localhost (needed for local git/gh) |
| `tools/base_tool.py` | Drop | Lifecycle overhead unnecessary; use `@server.tool()` directly |
| `core/*` | Drop entirely | LLM wrapper layer not needed |
| `tools/*` (v1) | Drop entirely | All tools redesigned |

### 2.6 v2 Config Schema

```python
class MCPConfig(BaseModel):
    server: ServerConfig       # host, port, debug (keep as-is)
    security: SecurityConfig   # allowed_paths, max_file_size, rate_limit (keep as-is)
    logging: LoggingConfig     # level, format, file_path (keep as-is)
    cache: CacheConfig         # enabled, ttl, cache_dir (keep as-is)

    # New: per-module enable/disable
    context: ContextModuleConfig   # enabled, cache_dir, supported_languages
    knowledge: KnowledgeModuleConfig # enabled, package_cache_ttl, doc_cache_ttl
    workflow: WorkflowModuleConfig   # enabled, default_repo_path
    specs: SpecsModuleConfig         # enabled, docs_root, templates_dir
```

Removed from v1: `AIConfig`, `CodeAnalyzerConfig`, `CodeGeneratorConfig`, `TestGeneratorConfig`, `DocGeneratorConfig`.

---

## 3. Module 1: Project Context

### 3.1 Tools

| Tool | Input | Output |
|------|-------|--------|
| `index_project` | `root_path`, `language?` | Project tree + function/class/module index |
| `get_symbol_info` | `symbol_name` | Definition location, type, references, parent module |
| `get_dependency_graph` | `file_path` or `module_name` | Upstream/downstream dependency adjacency list |
| `get_project_stats` | `root_path` | Language distribution, LOC, module count, complexity hotspots |

### 3.2 Implementation

- **code_indexer.py**: Python AST via `ast` module; JavaScript/TypeScript/Go/Java/Rust via `tree-sitter`. Index cached to local JSON, incremental update by comparing file mtime.
- **dependency_graph.py**: Parse `import` statements to build directed graph. Classify into stdlib / third-party / project-internal. Return adjacency list + depth info.
- **project_stats.py**: Walk directory, count lines by language (extension-based), compute cyclomatic complexity for Python (AST), heuristic for others.

### 3.3 Boundaries

- No LSP features (jump-to-definition, autocomplete) — AI IDE already has these
- No file watching — MCP is request-response; on-demand only

---

## 4. Module 2: External Knowledge

### 4.1 Tools

| Tool | Input | Output |
|------|-------|--------|
| `search_docs` | `query`, `library?`, `version?` | Matching doc fragments with links and code examples |
| `get_package_info` | `package_name`, `ecosystem` | Version, latest, changelog summary, deps, license |
| `search_code_examples` | `query`, `language` | Code snippets from public repos |
| `check_compatibility` | `project_path` | Conflict list, outdated packages, upgrade recommendations |

### 4.2 Implementation — CLI / Public HTTP API Only

- **doc_search.py**: `curl` to doc site search APIs (docs.rs, devdocs.io, MDN search endpoint). Fallback: `curl` + HTML parse for official doc sites.
- **package_info.py**:
  - Python → `pip index versions {pkg}` + `curl https://pypi.org/pypi/{pkg}/json`
  - Node → `npm view {pkg} --json`
  - Java → `curl` Maven Central Search API
  - Go → `go list -m -json {module}`
  - Rust → `curl https://crates.io/api/v1/crates/{pkg}`
- **code_search.py**: `gh search code {query} --language {lang} --json`
- **compatibility.py**:
  - Python → `pip check` + `pip list --outdated --format=json`
  - Node → `npm audit --json` + `npm outdated --json`
  - Java → `mvn dependency:tree` + `mvn versions:display-dependency-updates`
  - Go → `go mod tidy` + `go list -m -u all`
  - Rust → `cargo audit` + `cargo outdated`

### 4.3 Boundaries

- No doc summarization — return raw fragments, let AI summarize
- Cache TTL: package info 1 hour, docs 24 hours

---

## 5. Module 3: Dev Workflow

### 5.1 Tools

| Tool | Input | Output |
|------|-------|--------|
| `git_status` | `repo_path` | Branch, changed files, staging state, remote diff |
| `git_history` | `repo_path`, `file_path?`, `author?`, `since?` | Commit history with diff summary |
| `git_branch_analysis` | `repo_path` | Branch list, inter-branch diffs, merge status |
| `ci_status` | `repo_path` or `repo_url` | Recent CI runs, failed steps, log summary |
| `issue_list` | `repo_url`, `state?`, `labels?` | Issue list (title, labels, assignee, priority) |
| `pr_summary` | `repo_url`, `pr_number?` | PR list or single PR details (changed files, review status, conflicts) |

### 5.2 Implementation — git CLI + gh CLI

- **git_ops.py**:
  - `git_status`: `git status --porcelain` + `git rev-list --left-right --count HEAD...@{upstream}`
  - `git_history`: `git log --pretty=format:'{json}' --stat` with `--author`, `--since`, `-- {file}` filters
  - `git_branch_analysis`: `git branch -a --format='%(refname:short) %(upstream:track)'` + `git log --oneline {b1}..{b2}`
- **ci_github.py**:
  - `ci_status`: `gh run list --json` + `gh run view {id} --json`
  - `issue_list`: `gh issue list --json title,labels,assignees,state`
  - `pr_summary`: `gh pr list --json` or `gh pr view {number} --json`

### 5.3 Boundaries

- **Read-only** — no push, merge, reset, or CI trigger
- All destructive decisions left to the AI IDE and user

---

## 6. Module 4: Spec Management

### 6.1 Tools

| Tool | Input | Output |
|------|-------|--------|
| `list_specs` | `project_path`, `type?` | Spec file index (type, path, summary, updated_at) |
| `get_spec` | `spec_path` or `spec_name` | Full spec content + metadata |
| `search_specs` | `query`, `project_path` | Matching spec fragments with context |
| `create_spec` | `type`, `name`, `project_path` | Generated spec file path |
| `scaffold_project` | `template`, `target_path`, `params` | Generated directory structure + file list |
| `validate_structure` | `project_path`, `template?` | Diff report: current vs expected structure |

### 6.2 Standard Directory Convention

```
docs/
├── specs/           # Feature design documents
│   └── YYYY-MM-DD-<topic>-design.md
├── adr/             # Architecture Decision Records
│   └── ADR-NNN-<title>.md
├── guides/          # Developer guides
│   └── <topic>.md
├── api/             # API documentation
│   └── <module>.md
└── templates/       # Template files (for scaffold)
    ├── spec.md.tpl
    ├── adr.md.tpl
    └── module/      # Directory structure templates
        └── ...
```

### 6.3 Implementation

- **spec_manager.py**: Scan `docs/` directory, parse YAML frontmatter (`type`, `status`, `date`, `author`), build index. Filter by type (spec/adr/guide/api). Search via `grep` keyword matching.
- **scaffold.py**: Built-in multi-language project templates:
  - Python module: `__init__.py` + `main.py` + `tests/` + `README.md`
  - Node module: `index.ts` + `package.json` + `__tests__/` + `README.md`
  - Go module: `main.go` + `go.mod` + `*_test.go`
  - Rust module: `src/main.rs` + `Cargo.toml` + `tests/`
  - Generic: `src/` + `tests/` + `docs/` + `README.md`
  - Custom templates in `docs/templates/`
- **validator.py**: Diff current directory tree against template-defined expected structure, report missing/extra files.

### 6.4 Template Format

Simple `{{ var }}` substitution. Template definition in YAML:

```yaml
# docs/templates/module/template.yaml
name: python-module
description: Standard Python module structure
structure:
  - "{{ name }}/__init__.py"
  - "{{ name }}/main.py"
  - "{{ name }}/config.py"
  - "tests/test_{{ name }}.py"
  - "README.md"
variables:
  - name: Module name
  - author: Author (optional)
```

### 6.5 Boundaries

- No AI content generation — templates provide structure, AI IDE fills content
- No Git commit — generated files left for user to commit

---

## 7. External Dependencies

### 7.1 Python Packages

```
mcp-server-fastmcp>=0.9.0   # MCP framework
pydantic>=2.0.0              # Config management
tree-sitter>=0.20.0          # Multi-language AST parsing
tree-sitter-languages>=1.8.0 # Language grammars
pyyaml>=6.0                  # YAML frontmatter parsing
beautifulsoup4>=4.12.0       # HTML doc parsing
```

### 7.2 Required CLI Tools

| CLI | Used By | Required? |
|-----|---------|-----------|
| `git` | Workflow module | Yes |
| `gh` | CI/Issue/PR + code search | Yes |
| `pip`/`npm`/`go`/`cargo` | Package info + compatibility | Per language, on demand |
| `curl` | Doc search + public API calls | Yes |

---

## 8. Tool Summary

20 tools across 4 modules:

| # | Module | Tool | Read/Write |
|---|--------|------|------------|
| 1 | Context | `index_project` | Read |
| 2 | Context | `get_symbol_info` | Read |
| 3 | Context | `get_dependency_graph` | Read |
| 4 | Context | `get_project_stats` | Read |
| 5 | Knowledge | `search_docs` | Read |
| 6 | Knowledge | `get_package_info` | Read |
| 7 | Knowledge | `search_code_examples` | Read |
| 8 | Knowledge | `check_compatibility` | Read |
| 9 | Workflow | `git_status` | Read |
| 10 | Workflow | `git_history` | Read |
| 11 | Workflow | `git_branch_analysis` | Read |
| 12 | Workflow | `ci_status` | Read |
| 13 | Workflow | `issue_list` | Read |
| 14 | Workflow | `pr_summary` | Read |
| 15 | Specs | `list_specs` | Read |
| 16 | Specs | `get_spec` | Read |
| 17 | Specs | `search_specs` | Read |
| 18 | Specs | `create_spec` | Write |
| 19 | Specs | `scaffold_project` | Write |
| 20 | Specs | `validate_structure` | Read |
