import pytest
import tempfile
from utils.cache import FileCache

def test_cache_set_get():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCache(tmpdir, ttl=3600)
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

def test_cache_expired():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCache(tmpdir, ttl=0)
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result is None
