from config import MCPConfig, SecurityConfig
from pathlib import Path

def test_default_config():
    config = MCPConfig()
    assert config.server.host == "localhost"
    assert config.server.port == 8080
    assert config.security.max_file_size == 50 * 1024 * 1024

def test_security_validation():
    config = MCPConfig()
    assert config.security.validate_path("./src/main.py") is True


def test_security_validation_rejects_paths_outside_allowed_roots(tmp_path: Path):
    allowed = tmp_path / "workspace"
    allowed.mkdir()
    config = SecurityConfig(allowed_paths=[str(allowed)])

    assert config.validate_path(str(allowed / "src" / "main.py")) is True
    assert config.validate_path(str(allowed / ".." / "secret.txt")) is False
    assert config.validate_path(str(tmp_path / "workspace-copy" / "main.py")) is False
