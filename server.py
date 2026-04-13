#!/usr/bin/env python3
import asyncio
import sys
from mcp.server.fastmcp import FastMCP
from config import config
from tools.context.code_indexer import index_project, get_symbol_info
from tools.context.dependency_graph import get_dependency_graph
from tools.context.project_stats import get_project_stats

mcp = FastMCP(
    name="ai-coding",
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

async def main():
    print(f"AI Coding MCP v2 starting...")
    print(f"Server: {config.server.host}:{config.server.port}")
    await mcp.run()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
