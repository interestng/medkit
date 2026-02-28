from __future__ import annotations
import os
import json
import pickle
import hashlib
from typing import Any, Optional
from pathlib import Path

class BaseCache:
    def get(self, key: str) -> Any: raise NotImplementedError
    def set(self, key: str, value: Any): raise NotImplementedError

class MemoryCache(BaseCache):
    def __init__(self):
        self._data: dict[str, Any] = {}
    def get(self, key: str) -> Any: return self._data.get(key)
    def set(self, key: str, value: Any): self._data[key] = value

class DiskCache(BaseCache):
    def __init__(self, cache_dir: str = ".medkit_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_path(self, key: str) -> Path:
        hashed = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / hashed

    def get(self, key: str) -> Any:
        path = self._get_path(key)
        if path.exists():
            try:
                with open(path, "rb") as f:
                    return pickle.load(f)
            except (pickle.UnpicklingError, EOFError):
                 return None
        return None

    def set(self, key: str, value: Any):
        path = self._get_path(key)
        with open(path, "wb") as f:
            pickle.dump(value, f)
