from typing import List
from pathlib import Path
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=8080)
    debug: bool = Field(default=False)

class SecurityConfig(BaseModel):
    allowed_paths: List[str] = Field(default=["./"])
    max_file_size: int = Field(default=50*1024*1024)

    def validate_path(self, path: str) -> bool:
        try:
            resolved = Path(path).expanduser().resolve()
            for allowed_path in self.allowed_paths:
                allowed = Path(allowed_path).expanduser().resolve()
                try:
                    resolved.relative_to(allowed)
                    return True
                except ValueError:
                    continue
        except (OSError, RuntimeError, ValueError):
            return False
        return False

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
