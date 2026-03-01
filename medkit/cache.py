from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MemoryCache:
    """In-memory Time-To-Live (TTL) cache."""

    def __init__(self, default_ttl: int = 3600):
        self._data: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        if key not in self._data:
            return None

        entry = self._data[key]
        if time.time() > entry["expires_at"]:
            del self._data[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl or self.default_ttl
        self._data[key] = {"value": value, "expires_at": time.time() + ttl}


class DiskCache:
    """Persistent JSON-based cache for medical data."""

    def __init__(self, cache_dir: str = ".medkit_cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_path(self, key: str) -> str:
        # Simple hash-based filename to avoid illegal characters in keys
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if time.time() > data.get("expires_at", 0):
                os.remove(path)
                return None
            return data["value"]
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        path = self._get_path(key)

        # Handle Pydantic models by converting to dict
        if isinstance(value, BaseModel):
            value_to_store = value.model_dump()
        else:
            value_to_store = value

        data = {
            "value": value_to_store,
            "expires_at": time.time() + ttl,
            "key": key,  # For debugging
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass
