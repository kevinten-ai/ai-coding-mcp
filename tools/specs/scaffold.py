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
            "tests/test_{{ name }}.py": "import pytest\nfrom {{ name }} import main\n\ndef test_main():\n    assert main() is None\n",
            "README.md": "# {{ name }}\n\nTODO: Add description\n"
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
            "package.json": '{\n  \"name\": \"{{ name }}\",\n  \"version\": \"0.1.0\",\n  \"main\": \"dist/index.js\",\n  \"scripts\": {\n    \"build\": \"tsc\",\n    \"test\": \"jest\"\n  }\n}\n',
            "README.md": "# {{ name }}\n\nTODO: Add description\n"
        }
    },
    "generic": {
        "structure": ["src/", "tests/", "docs/", "README.md"],
        "files": {"README.md": "# {{ name }}\n\nTODO: Add description\n"}
    }
}

async def scaffold_project(template: str, target_path: str, params: dict) -> dict:
    try:
        if template not in TEMPLATES:
            return {"success": False, "error": {"code": "UNKNOWN_TEMPLATE", "message": f"Unknown template: {template}"}}
        if "name" not in params:
            return {"success": False, "error": {"code": "MISSING_PARAM", "message": "Missing required param: name"}}
        tmpl = TEMPLATES[template]
        target = Path(target_path)
        target.mkdir(parents=True, exist_ok=True)
        created = []
        for item in tmpl["structure"]:
            path = target / item.replace("{{ name }}", params["name"])
            if "." not in path.name:
                path.mkdir(parents=True, exist_ok=True)
                created.append(str(path))
        for file_path, content in tmpl["files"].items():
            full_path = target / file_path.replace("{{ name }}", params["name"])
            full_path.parent.mkdir(parents=True, exist_ok=True)
            final_content = content
            for key, value in params.items():
                final_content = final_content.replace(f"{{{{ {key} }}}}", value)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            created.append(str(full_path))
        return {"success": True, "data": {"created_files": created}}
    except Exception as e:
        return {"success": False, "error": {"code": "UNKNOWN", "message": str(e)}}
