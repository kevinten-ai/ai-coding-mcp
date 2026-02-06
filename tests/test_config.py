"""
配置文件测试
"""

import pytest
from ..config import config, MCPConfig, AIConfig


class TestConfig:
    """配置测试"""

    def test_config_initialization(self):
        """测试配置初始化"""
        assert isinstance(config, MCPConfig)
        assert config.server.host == "localhost"
        assert config.server.port == 8080

    def test_ai_config(self):
        """测试AI配置"""
        assert isinstance(config.ai, AIConfig)
        assert config.ai.model in ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2"]

    def test_server_config(self):
        """测试服务器配置"""
        assert config.server.host is not None
        assert config.server.port > 0
        assert isinstance(config.server.debug, bool)

    def test_security_config(self):
        """测试安全配置"""
        assert config.security.max_file_size > 0
        assert isinstance(config.security.allowed_paths, list)
        assert isinstance(config.security.blocked_extensions, list)



