import json
from utils.cli_runner import run_cli

async def git_status(repo_path: str) -> dict:
    try:
        branch_result = await run_cli(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path, timeout=10)
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
        status_result = await run_cli(["git", "status", "--porcelain"], cwd=repo_path, timeout=10)
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
        return {"success": True, "data": {"branch": branch, "changed": changed, "staged": staged}}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}

async def git_history(repo_path: str, file_path: str = None, author: str = None, since: str = None) -> dict:
    try:
        cmd = ["git", "log", '--pretty=format:{"hash":"%h","author":"%an","date":"%ad","message":"%s"}', "--date=short", "-n", "20"]
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
                        commits.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return {"success": True, "data": {"commits": commits}}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}

async def git_branch_analysis(repo_path: str) -> dict:
    return {"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Branch analysis not yet implemented"}}
