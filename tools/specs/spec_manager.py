import os
import datetime
from pathlib import Path
from typing import Optional

def _parse_frontmatter(content: str) -> tuple:
    frontmatter = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            content = parts[2].strip()
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
    return frontmatter, content

def _get_summary(content: str, max_length: int = 100) -> str:
    for line in content.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            return line[:max_length] + ('...' if len(line) > max_length else '')
    return ""

async def list_specs(project_path: str, spec_type: str = None) -> dict:
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
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}

async def get_spec(project_path: str, spec_path: str) -> dict:
    try:
        full_path = Path(project_path) / spec_path
        if not full_path.exists():
            return {"success": False, "error": {"code": "FILE_NOT_FOUND", "message": f"Spec not found: {spec_path}"}}
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        frontmatter, body = _parse_frontmatter(content)
        return {"success": True, "data": {"content": body, "frontmatter": frontmatter, "path": spec_path}}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}

async def search_specs(project_path: str, query: str) -> dict:
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
                    idx = content.find(query_lower)
                    start = max(0, idx - 50)
                    end = min(len(content), idx + len(query) + 50)
                    context = spec_detail["data"]["content"][start:end]
                    results.append({"path": spec["path"], "context": context, "type": spec["type"]})
        return {"success": True, "data": {"results": results}}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}

async def create_spec(project_path: str, spec_type: str, name: str) -> dict:
    try:
        type_dir = {"spec": "specs", "adr": "adr", "guide": "guides", "api": "api"}
        if spec_type not in type_dir:
            return {"success": False, "error": {"code": "INVALID_TYPE", "message": f"Unknown spec type: {spec_type}"}}
        dir_path = Path(project_path) / "docs" / type_dir[spec_type]
        dir_path.mkdir(parents=True, exist_ok=True)
        today = datetime.date.today()
        if spec_type == "spec":
            filename = f"{today.strftime('%Y-%m-%d')}-{name}.md"
        elif spec_type == "adr":
            filename = f"ADR-001-{name}.md"
        else:
            filename = f"{name}.md"
        file_path = dir_path / filename
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
        return {"success": True, "data": {"path": str(file_path.relative_to(project_path))}}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}
