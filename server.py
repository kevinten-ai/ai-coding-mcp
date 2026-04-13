#!/usr/bin/env python3
import asyncio
import sys
from mcp.server.fastmcp import FastMCP
from config import config
from tools.context.code_indexer import index_project, get_symbol_info
from tools.context.dependency_graph import get_dependency_graph
from tools.context.project_stats import get_project_stats
from tools.knowledge.doc_search import search_docs
from tools.knowledge.package_info import get_package_info
from tools.knowledge.code_search import search_code_examples
from tools.knowledge.compatibility import check_compatibility
from tools.workflow.git_ops import git_status, git_history, git_branch_analysis
from tools.workflow.ci_github import ci_status, issue_list, pr_summary

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

async def main():
    print(f"AI Coding MCP v2 starting...")
    print(f"Server: {config.server.host}:{config.server.port}")
    await mcp.run()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
