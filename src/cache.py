"""In-memory cache with TTL. Drops in as Redis replacement for Render free tier."""
import time


class MemoryCache:
    def __init__(self):
        self._store = {}

    def get(self, key):
        entry = self._store.get(key)
        if entry and (entry["exp"] == 0 or entry["exp"] > time.time()):
            return entry["val"]
        if entry:
            del self._store[key]
        return None

    def set(self, key, val, ttl=30):
        self._store[key] = {"val": val, "exp": time.time() + ttl if ttl > 0 else 0}

    def delete(self, key):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()

    def keys(self, pattern=None):
        return list(self._store.keys())


cache = MemoryCache()
