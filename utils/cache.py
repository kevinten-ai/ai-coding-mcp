import json
import hashlib
import time
from pathlib import Path
from typing import Any, Optional

class FileCache:
    def __init__(self, cache_dir: str, ttl: int = 3600):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

    def _get_cache_path(self, key: str) -> Path:
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[Any]:
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
            if time.time() - cached.get('timestamp', 0) > self.ttl:
                cache_path.unlink(missing_ok=True)
                return None
            return cached.get('data')
        except (json.JSONDecodeError, IOError):
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any) -> None:
        cache_path = self._get_cache_path(key)
        with open(cache_path, 'w') as f:
            json.dump({'timestamp': time.time(), 'data': value}, f)

    def clear(self) -> None:
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink(missing_ok=True)
