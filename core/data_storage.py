"""
数据存储器
处理数据的本地持久化和检索
"""

import json
import sqlite3
import asyncio
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import pickle
from enum import Enum

from ..config import config


class StorageFormat(Enum):
    """存储格式"""
    JSON = "json"
    PICKLE = "pickle"
    SQLITE = "sqlite"


@dataclass
class StorageItem:
    """存储项"""
    key: str
    data: Any
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def is_expired(self) -> bool:
        """检查是否过期"""
        return self.expires_at is not None and datetime.now() > self.expires_at

    def touch(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = datetime.now()
        self.updated_at = datetime.now()


class CacheStorage:
    """缓存存储"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = ttl
        self._cache: Dict[str, StorageItem] = {}
        self._access_order: List[str] = []

    def _generate_key(self, data: Any) -> str:
        """生成缓存键"""
        if isinstance(data, str):
            content = data.encode('utf-8')
        elif isinstance(data, dict):
            content = json.dumps(data, sort_keys=True).encode('utf-8')
        else:
            content = pickle.dumps(data)

        return hashlib.md5(content).hexdigest()

    async def set(self, key: str, data: Any,
                  ttl: Optional[int] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        设置缓存项

        Args:
            key: 缓存键
            data: 数据
            ttl: 生存时间（秒）
            metadata: 元数据

        Returns:
            bool: 是否成功
        """
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl or self.default_ttl) if ttl != 0 else None

        item = StorageItem(
            key=key,
            data=data,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            expires_at=expires_at
        )

        # 检查容量限制
        if key not in self._cache and len(self._cache) >= self.max_size:
            await self._evict_oldest()

        self._cache[key] = item

        # 更新访问顺序
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return True

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存项

        Args:
            key: 缓存键

        Returns:
            Optional[Any]: 缓存数据
        """
        if key not in self._cache:
            return None

        item = self._cache[key]

        # 检查是否过期
        if item.is_expired():
            await self.delete(key)
            return None

        # 更新访问信息
        item.touch()

        # 更新访问顺序
        self._access_order.remove(key)
        self._access_order.append(key)

        return item.data

    async def delete(self, key: str) -> bool:
        """
        删除缓存项

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功
        """
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False

    async def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()

    async def _evict_oldest(self):
        """淘汰最旧的缓存项（LRU策略）"""
        if self._access_order:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_access = sum(item.access_count for item in self._cache.values())
        expired_count = sum(1 for item in self._cache.values() if item.is_expired())

        return {
            "total_items": len(self._cache),
            "max_size": self.max_size,
            "total_access_count": total_access,
            "expired_items": expired_count,
            "hit_rate": total_access / max(len(self._cache), 1)
        }


class FileStorage:
    """文件存储"""

    def __init__(self, base_dir: str = "./data", format: StorageFormat = StorageFormat.JSON):
        self.base_dir = Path(base_dir)
        self.format = format
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """获取文件路径"""
        # 创建子目录避免单个目录文件过多
        sub_dir = key[:2] if len(key) >= 2 else "default"
        dir_path = self.base_dir / sub_dir
        dir_path.mkdir(exist_ok=True)

        extension = {
            StorageFormat.JSON: ".json",
            StorageFormat.PICKLE: ".pkl",
            StorageFormat.SQLITE: ".db"
        }.get(self.format, ".json")

        return dir_path / f"{key}{extension}"

    async def save(self, key: str, data: Any,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        保存数据到文件

        Args:
            key: 数据键
            data: 数据
            metadata: 元数据

        Returns:
            bool: 是否成功
        """
        try:
            file_path = self._get_file_path(key)

            if self.format == StorageFormat.JSON:
                content = {
                    "key": key,
                    "data": data,
                    "metadata": metadata or {},
                    "saved_at": datetime.now().isoformat()
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2, default=str)

            elif self.format == StorageFormat.PICKLE:
                with open(file_path, 'wb') as f:
                    pickle.dump({
                        "key": key,
                        "data": data,
                        "metadata": metadata or {},
                        "saved_at": datetime.now()
                    }, f)

            return True

        except Exception as e:
            print(f"Failed to save data for key {key}: {e}")
            return False

    async def load(self, key: str) -> Optional[Any]:
        """
        从文件加载数据

        Args:
            key: 数据键

        Returns:
            Optional[Any]: 加载的数据
        """
        try:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                return None

            if self.format == StorageFormat.JSON:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                return content.get("data")

            elif self.format == StorageFormat.PICKLE:
                with open(file_path, 'rb') as f:
                    content = pickle.load(f)
                return content.get("data")

        except Exception as e:
            print(f"Failed to load data for key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """
        删除数据文件

        Args:
            key: 数据键

        Returns:
            bool: 是否成功
        """
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            print(f"Failed to delete data for key {key}: {e}")
            return False

    async def list_keys(self, prefix: str = "") -> List[str]:
        """
        列出所有键

        Args:
            prefix: 键前缀

        Returns:
            List[str]: 键列表
        """
        keys = []
        try:
            for file_path in self.base_dir.rglob("*"):
                if file_path.is_file():
                    # 从文件名提取键
                    filename = file_path.stem
                    if filename.startswith(prefix):
                        keys.append(filename)
        except Exception as e:
            print(f"Failed to list keys: {e}")

        return keys


class DataStorage:
    """
    数据存储器

    提供统一的数据持久化和检索接口：
    - 多层存储策略（内存缓存 + 文件存储）
    - 自动过期和清理机制
    - 数据压缩和序列化
    """

    def __init__(self):
        self.cache = CacheStorage(
            max_size=config.cache.max_size,
            ttl=config.cache.ttl
        )
        self.file_storage = FileStorage(
            base_dir=config.cache.cache_dir,
            format=StorageFormat.JSON
        )
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """初始化存储器"""
        # 启动定期清理任务
        if config.cache.enabled:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def shutdown(self):
        """关闭存储器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def store(self, key: str, data: Any,
                   use_cache: bool = True,
                   persist: bool = True,
                   ttl: Optional[int] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        存储数据

        Args:
            key: 数据键
            data: 数据
            use_cache: 是否使用缓存
            persist: 是否持久化存储
            ttl: 生存时间（秒）
            metadata: 元数据

        Returns:
            bool: 是否成功
        """
        success = True

        # 缓存存储
        if use_cache and config.cache.enabled:
            cache_success = await self.cache.set(key, data, ttl, metadata)
            success = success and cache_success

        # 文件存储
        if persist:
            file_success = await self.file_storage.save(key, data, metadata)
            success = success and file_success

        return success

    async def retrieve(self, key: str,
                      use_cache: bool = True,
                      fallback_to_file: bool = True) -> Optional[Any]:
        """
        检索数据

        Args:
            key: 数据键
            use_cache: 是否检查缓存
            fallback_to_file: 是否回退到文件存储

        Returns:
            Optional[Any]: 检索到的数据
        """
        # 首先检查缓存
        if use_cache and config.cache.enabled:
            data = await self.cache.get(key)
            if data is not None:
                return data

        # 回退到文件存储
        if fallback_to_file:
            return await self.file_storage.load(key)

        return None

    async def remove(self, key: str,
                    from_cache: bool = True,
                    from_file: bool = True) -> bool:
        """
        删除数据

        Args:
            key: 数据键
            from_cache: 是否从缓存删除
            from_file: 是否从文件删除

        Returns:
            bool: 是否成功
        """
        success = True

        if from_cache and config.cache.enabled:
            success = success and await self.cache.delete(key)

        if from_file:
            success = success and await self.file_storage.delete(key)

        return success

    async def exists(self, key: str) -> bool:
        """
        检查数据是否存在

        Args:
            key: 数据键

        Returns:
            bool: 是否存在
        """
        # 检查缓存
        if config.cache.enabled:
            data = await self.cache.get(key)
            if data is not None:
                return True

        # 检查文件存储
        return await self.file_storage.load(key) is not None

    async def list_keys(self, prefix: str = "") -> List[str]:
        """
        列出所有键

        Args:
            prefix: 键前缀

        Returns:
            List[str]: 键列表
        """
        return await self.file_storage.list_keys(prefix)

    async def clear_cache(self):
        """清空缓存"""
        if config.cache.enabled:
            await self.cache.clear()

    async def clear_all(self):
        """清空所有存储"""
        await self.clear_cache()
        # 注意：文件存储的清空需要谨慎处理，这里暂时不实现

    async def _periodic_cleanup(self):
        """定期清理过期数据"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次

                if config.cache.enabled:
                    # 这里可以实现更复杂的清理逻辑
                    # 例如清理过期的缓存项、压缩文件等
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error during periodic cleanup: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        cache_stats = self.cache.get_stats() if config.cache.enabled else {}

        return {
            "cache": cache_stats,
            "cache_enabled": config.cache.enabled,
            "file_storage_dir": str(self.file_storage.base_dir),
            "storage_format": self.file_storage.format.value
        }



