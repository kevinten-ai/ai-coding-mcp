"""
MCP服务器配置文件
基于Pydantic的类型安全配置管理
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import os


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = Field(default="localhost", description="服务器主机地址")
    port: int = Field(default=8080, description="服务器端口")
    ssl: bool = Field(default=False, description="是否启用SSL")
    workers: int = Field(default=4, description="工作进程数")
    debug: bool = Field(default=False, description="调试模式")


class ToolConfig(BaseModel):
    """工具配置"""
    enabled: bool = Field(default=True, description="是否启用工具")
    timeout: int = Field(default=30, description="工具执行超时时间(秒)")
    max_concurrent: int = Field(default=5, description="最大并发执行数")


class CodeAnalyzerConfig(ToolConfig):
    """代码分析工具配置"""
    languages: List[str] = Field(default=["python", "javascript", "java", "typescript"],
                               description="支持的编程语言")
    max_file_size: int = Field(default=10*1024*1024, description="最大文件大小(字节)")
    exclude_patterns: List[str] = Field(default=["*.pyc", "__pycache__/**", "node_modules/**"],
                                       description="排除的文件模式")


class CodeGeneratorConfig(ToolConfig):
    """代码生成工具配置"""
    templates_dir: str = Field(default="./templates", description="模板目录")
    max_output_length: int = Field(default=2000, description="最大输出长度")
    supported_languages: List[str] = Field(default=["python", "javascript", "java"],
                                          description="支持的输出语言")


class TestGeneratorConfig(ToolConfig):
    """测试生成工具配置"""
    frameworks: Dict[str, List[str]] = Field(
        default={
            "python": ["pytest", "unittest"],
            "javascript": ["jest", "mocha"],
            "java": ["junit", "testng"]
        },
        description="各语言支持的测试框架"
    )
    coverage_target: float = Field(default=0.8, description="目标测试覆盖率")


class DocGeneratorConfig(ToolConfig):
    """文档生成工具配置"""
    formats: List[str] = Field(default=["markdown", "html"], description="支持的文档格式")
    include_examples: bool = Field(default=True, description="是否包含代码示例")
    auto_commit: bool = Field(default=False, description="是否自动提交文档变更")


class AIConfig(BaseModel):
    """AI配置"""
    provider: str = Field(default="openai", description="AI提供商")
    model: str = Field(default="gpt-4", description="使用的模型")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=2000, gt=0, description="最大token数")
    timeout: int = Field(default=60, description="请求超时时间(秒)")

    @validator('api_key', always=True)
    def validate_api_key(cls, v):
        """验证API密钥"""
        if v is None:
            # 尝试从环境变量获取
            env_key = os.getenv('AI_API_KEY')
            if env_key:
                return env_key
            # 如果是本地开发环境，可以设置默认值
            if os.getenv('ENV') == 'development':
                return 'dev-key-placeholder'
        return v


class SecurityConfig(BaseModel):
    """安全配置"""
    allowed_paths: List[str] = Field(default=["./"], description="允许访问的路径")
    max_file_size: int = Field(default=50*1024*1024, description="最大文件大小(字节)")
    rate_limit_requests: int = Field(default=60, description="每分钟请求限制")
    rate_limit_burst: int = Field(default=10, description="突发请求限制")
    enable_path_validation: bool = Field(default=True, description="启用路径验证")
    blocked_extensions: List[str] = Field(default=[".exe", ".bat", ".cmd", ".com"],
                                         description="禁止的文件扩展名")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                       description="日志格式")
    file_path: Optional[str] = Field(default="logs/mcp_server.log", description="日志文件路径")
    max_file_size: int = Field(default=10*1024*1024, description="最大日志文件大小")
    backup_count: int = Field(default=5, description="日志文件备份数量")


class CacheConfig(BaseModel):
    """缓存配置"""
    enabled: bool = Field(default=True, description="启用缓存")
    ttl: int = Field(default=3600, description="缓存过期时间(秒)")
    max_size: int = Field(default=1000, description="最大缓存条目数")
    cache_dir: str = Field(default="./cache", description="缓存目录")


class MCPConfig(BaseModel):
    """主配置类"""
    server: ServerConfig = Field(default_factory=ServerConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

    # 工具配置
    code_analyzer: CodeAnalyzerConfig = Field(default_factory=CodeAnalyzerConfig)
    code_generator: CodeGeneratorConfig = Field(default_factory=CodeGeneratorConfig)
    test_generator: TestGeneratorConfig = Field(default_factory=TestGeneratorConfig)
    doc_generator: DocGeneratorConfig = Field(default_factory=DocGeneratorConfig)

    class Config:
        """Pydantic配置"""
        validate_assignment = True
        arbitrary_types_allowed = True


# 全局配置实例
config = MCPConfig()


def load_config_from_file(file_path: str = "config.yaml") -> MCPConfig:
    """
    从YAML文件加载配置

    Args:
        file_path: 配置文件路径

    Returns:
        MCPConfig: 配置对象
    """
    try:
        import yaml
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return MCPConfig(**data)
    except ImportError:
        print("Warning: PyYAML not installed, skipping config file loading")
    except Exception as e:
        print(f"Warning: Failed to load config from {file_path}: {e}")

    return config


def save_config_to_file(config: MCPConfig, file_path: str = "config.yaml"):
    """
    保存配置到YAML文件

    Args:
        config: 配置对象
        file_path: 保存路径
    """
    try:
        import yaml
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config.dict(), f, default_flow_style=False, allow_unicode=True)
    except ImportError:
        print("Warning: PyYAML not installed, skipping config file saving")
    except Exception as e:
        print(f"Warning: Failed to save config to {file_path}: {e}")


# 开发环境配置
def get_development_config() -> MCPConfig:
    """获取开发环境配置"""
    dev_config = MCPConfig()
    dev_config.server.debug = True
    dev_config.logging.level = "DEBUG"
    dev_config.ai.api_key = "dev-key-placeholder"
    return dev_config


# 生产环境配置
def get_production_config() -> MCPConfig:
    """获取生产环境配置"""
    prod_config = MCPConfig()
    prod_config.server.ssl = True
    prod_config.server.workers = 8
    prod_config.logging.level = "WARNING"
    return prod_config


# 根据环境变量自动选择配置
def get_config_by_env() -> MCPConfig:
    """根据环境变量获取配置"""
    env = os.getenv('ENV', 'development').lower()

    if env == 'production':
        return get_production_config()
    elif env == 'testing':
        test_config = get_development_config()
        test_config.server.debug = False
        return test_config
    else:
        return get_development_config()


# 初始化配置
if __name__ == "__main__":
    # 尝试从文件加载，否则使用默认配置
    config = load_config_from_file()

    # 打印当前配置
    print("Current Configuration:")
    print(f"Server: {config.server.host}:{config.server.port}")
    print(f"AI Model: {config.ai.model}")
    print(f"Debug Mode: {config.server.debug}")



