"""In-memory TTL cache and single-flight guard for the digest pipeline.

Thread-safe: FastAPI sync endpoints and `BackgroundTasks` both run on the
threadpool, so both structures lock around mutation.
"""
import threading
import time

import config


class TTLCache:
    def __init__(self, ttl: float):
        self._ttl = ttl
        self._data: dict[tuple, tuple] = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() < expires_at:
                return value
            self._data.pop(key, None)
            return None

    def set(self, key, value):
        with self._lock:
            self._data[key] = (value, time.monotonic() + self._ttl)

    def invalidate(self, key):
        with self._lock:
            self._data.pop(key, None)


class SingleFlight:
    def __init__(self):
        self._lock = threading.Lock()
        self._active: set[int] = set()

    def acquire(self, key) -> bool:
        """Atomically claim `key` for a run; False if already claimed."""
        with self._lock:
            if key in self._active:
                return False
            self._active.add(key)
            return True

    def release(self, key):
        with self._lock:
            self._active.discard(key)

    def is_active(self, key) -> bool:
        with self._lock:
            return key in self._active


cache = TTLCache(config.REFRESH_CACHE_TTL_SECONDS)
inflight = SingleFlight()
