"""
安全验证工具
提供路径验证、文件大小检查等安全功能
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Set
from urllib.parse import urlparse

from ..config import config


class SecurityValidator:
    """
    安全验证器

    提供全面的安全验证功能：
    - 路径遍历攻击防护
    - 文件大小限制
    - 文件类型验证
    - URL安全性检查
    """

    def __init__(self):
        self.allowed_paths = set(config.security.allowed_paths)
        self.max_file_size = config.security.max_file_size
        self.blocked_extensions = set(config.security.blocked_extensions)

    def validate_file_path(self, file_path: str, base_path: Optional[str] = None) -> bool:
        """
        验证文件路径安全性

        Args:
            file_path: 要验证的文件路径
            base_path: 基准路径

        Returns:
            bool: 是否安全

        Raises:
            SecurityError: 路径不安全
        """
        # 解析路径
        try:
            path = Path(file_path).resolve()
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid file path: {e}")

        # 检查路径遍历攻击
        if ".." in file_path or not self._is_path_safe(path):
            raise SecurityError("Path traversal detected")

        # 检查是否在允许的路径范围内
        if not self._is_path_allowed(path):
            raise SecurityError(f"Path not allowed: {path}")

        # 检查文件扩展名
        if path.suffix.lower() in self.blocked_extensions:
            raise SecurityError(f"File extension not allowed: {path.suffix}")

        return True

    def validate_file_size(self, file_path: str) -> bool:
        """
        验证文件大小

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否在允许范围内

        Raises:
            SecurityError: 文件过大
        """
        try:
            size = os.path.getsize(file_path)
            if size > self.max_file_size:
                raise SecurityError(
                    f"File too large: {size} bytes > {self.max_file_size} bytes"
                )
            return True
        except OSError as e:
            raise SecurityError(f"Cannot get file size: {e}")

    def validate_content(self, content: str, content_type: str = "code") -> bool:
        """
        验证内容安全性

        Args:
            content: 内容
            content_type: 内容类型

        Returns:
            bool: 是否安全

        Raises:
            SecurityError: 内容不安全
        """
        if len(content) > self.max_file_size:
            raise SecurityError("Content too large")

        # 检查恶意内容模式
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS脚本
            r'javascript:',                # JavaScript URL
            r'data:',                      # Data URL
            r'vbscript:',                  # VBScript
            r'on\w+\s*=',                  # 事件处理器
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                raise SecurityError(f"Dangerous content detected: {pattern}")

        return True

    def validate_url(self, url: str) -> bool:
        """
        验证URL安全性

        Args:
            url: 要验证的URL

        Returns:
            bool: 是否安全

        Raises:
            SecurityError: URL不安全
        """
        try:
            parsed = urlparse(url)

            # 检查scheme
            if parsed.scheme not in ['http', 'https']:
                raise SecurityError(f"Invalid URL scheme: {parsed.scheme}")

            # 检查主机名
            if not parsed.hostname:
                raise SecurityError("Missing hostname in URL")

            # 检查可疑主机名
            suspicious_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
            if parsed.hostname in suspicious_hosts:
                raise SecurityError(f"Suspicious hostname: {parsed.hostname}")

            return True

        except Exception as e:
            raise SecurityError(f"Invalid URL: {e}")

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不安全字符

        Args:
            filename: 原始文件名

        Returns:
            str: 清理后的文件名
        """
        # 移除路径分隔符
        filename = re.sub(r'[\/\\]', '', filename)

        # 移除其他不安全字符
        filename = re.sub(r'[<>:"|?*]', '', filename)

        # 限制长度
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext

        return filename

    def _is_path_safe(self, path: Path) -> bool:
        """
        检查路径是否安全（无路径遍历）

        Args:
            path: 路径对象

        Returns:
            bool: 是否安全
        """
        try:
            # 解析绝对路径并检查
            resolved = path.resolve()
            return resolved.exists() or not ".." in str(path)
        except (OSError, ValueError):
            return False

    def _is_path_allowed(self, path: Path) -> bool:
        """
        检查路径是否在允许范围内

        Args:
            path: 路径对象

        Returns:
            bool: 是否允许
        """
        if not self.allowed_paths:
            return True  # 如果没有设置允许路径，则允许所有

        path_str = str(path)

        for allowed_path in self.allowed_paths:
            allowed = Path(allowed_path)
            try:
                # 检查是否是子路径
                path.relative_to(allowed)
                return True
            except ValueError:
                continue

        return False


class RateLimiter:
    """
    速率限制器

    防止API滥用和DoS攻击
    """

    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.requests = []

    def is_allowed(self, identifier: str) -> bool:
        """
        检查是否允许请求

        Args:
            identifier: 请求标识符（如IP地址、用户ID）

        Returns:
            bool: 是否允许
        """
        import time
        current_time = time.time()

        # 清理过期请求
        cutoff_time = current_time - 60  # 1分钟
        self.requests = [req for req in self.requests if req[1] > cutoff_time]

        # 统计当前请求数
        recent_requests = [req for req in self.requests if req[0] == identifier]

        # 检查速率限制
        if len(recent_requests) >= self.requests_per_minute:
            return False

        # 检查突发限制（更短时间窗口）
        burst_window = current_time - 10  # 10秒
        burst_requests = [req for req in recent_requests if req[1] > burst_window]
        if len(burst_requests) >= self.burst_limit:
            return False

        # 记录请求
        self.requests.append((identifier, current_time))

        return True


class SecurityError(Exception):
    """安全异常"""
    pass


# 全局安全验证器实例
security_validator = SecurityValidator()
rate_limiter = RateLimiter(
    requests_per_minute=config.security.rate_limit_requests,
    burst_limit=config.security.rate_limit_burst
)



