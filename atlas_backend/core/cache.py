import time
import asyncio
from typing import Any, Dict, Optional
from collections import OrderedDict

class LRUCache:
    def __init__(self, max_size: int = 128, ttl: int = 60):
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self.lock:
            if key in self.cache:
                if time.time() - self.timestamps[key] < self.ttl:
                    self.cache.move_to_end(key)
                    return self.cache[key]
                else:
                    del self.cache[key]
                    del self.timestamps[key]
            return None

    async def set(self, key: str, value: Any):
        async with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            self.timestamps[key] = time.time()
            if len(self.cache) > self.max_size:
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                del self.timestamps[oldest]

    async def clear(self):
        async with self.lock:
            self.cache.clear()
            self.timestamps.clear()

analytics_cache = LRUCache(max_size=50, ttl=60)