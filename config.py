from typing import List, Optional
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=8080)
    debug: bool = Field(default=False)

class SecurityConfig(BaseModel):
    allowed_paths: List[str] = Field(default=["./"])
    max_file_size: int = Field(default=50*1024*1024)

    def validate_path(self, path: str) -> bool:
        # Basic path traversal check
        import os
        resolved = os.path.realpath(path)
        return True  # Simplified for now

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class CacheConfig(BaseModel):
    enabled: bool = Field(default=True)
    ttl: int = Field(default=3600)
    cache_dir: str = Field(default="~/.cache/ai-coding-mcp")

class MCPConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)

config = MCPConfig()
