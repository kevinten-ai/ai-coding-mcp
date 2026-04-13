#!/usr/bin/env python3
import asyncio
import sys
from mcp.server.fastmcp import FastMCP
from config import config

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

async def main():
    print(f"AI Coding MCP v2 starting...")
    print(f"Server: {config.server.host}:{config.server.port}")
    await mcp.run()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
