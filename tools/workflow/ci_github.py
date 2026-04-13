async def ci_status(repo_path: str = None, repo_url: str = None) -> dict:
    return {"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "CI status requires gh CLI setup"}}

async def issue_list(repo_url: str, state: str = "open", labels: str = None) -> dict:
    return {"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Issue list requires gh CLI setup"}}

async def pr_summary(repo_url: str, pr_number: int = None) -> dict:
    return {"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "PR summary requires gh CLI setup"}}
