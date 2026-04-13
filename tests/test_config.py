from config import MCPConfig, ServerConfig, SecurityConfig

def test_default_config():
    config = MCPConfig()
    assert config.server.host == "localhost"
    assert config.server.port == 8080
    assert config.security.max_file_size == 50 * 1024 * 1024

def test_security_validation():
    config = MCPConfig()
    assert config.security.validate_path("./src/main.py") is True
