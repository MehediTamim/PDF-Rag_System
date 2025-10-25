import time
import hashlib
from typing import Optional, Dict, Any

logger = None

def _get_logger():
    global logger
    if logger is None:
        from utils.logger import Logger
        logger = Logger.get_logger('cache')
    return logger


class QueryCache:
    def __init__(self, ttl: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
        self.hit_count = 0
        self.miss_count = 0
        _get_logger().info(f"Query cache initialized (TTL: {ttl}s)")
    
    def _generate_key(self, collection_name: str, query: str, search_type: str = 'semantic') -> str:
        raw_key = f"{collection_name}:{search_type}:{query.lower().strip()}"
        return hashlib.md5(raw_key.encode()).hexdigest()
    
    def get(self, collection_name: str, query: str, search_type: str = 'semantic') -> Optional[list]:
        try:
            key = self._generate_key(collection_name, query, search_type)
            
            if key in self._cache:
                cache_entry = self._cache[key]
                
                if time.time() - cache_entry['timestamp'] < self.ttl:
                    self.hit_count += 1
                    _get_logger().debug(f"Cache HIT for query: {query[:50]}...")
                    return cache_entry['results']
                else:
                    del self._cache[key]
                    _get_logger().debug(f"Cache EXPIRED for query: {query[:50]}...")
            
            self.miss_count += 1
            _get_logger().debug(f"Cache MISS for query: {query[:50]}...")
            return None
        
        except Exception as e:
            _get_logger().error(f"Error getting from cache: {e}")
            return None
    
    def set(self, collection_name: str, query: str, results: list, search_type: str = 'semantic'):
        try:
            key = self._generate_key(collection_name, query, search_type)
            self._cache[key] = {
                'results': results,
                'timestamp': time.time(),
                'query': query,
                'collection': collection_name
            }
            _get_logger().debug(f"Cache SET for query: {query[:50]}...")
        except Exception as e:
            _get_logger().error(f"Error setting cache: {e}")
    
    def clear_collection(self, collection_name: str):
        try:
            keys_to_delete = [
                k for k, v in self._cache.items() 
                if v.get('collection') == collection_name
            ]
            for key in keys_to_delete:
                del self._cache[key]
            _get_logger().info(f"Cleared cache for collection: {collection_name}")
        except Exception as e:
            _get_logger().error(f"Error clearing collection cache: {e}")
    
    def clear_all(self):
        self._cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        _get_logger().info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        
        return {
            'cache_size': len(self._cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.2f}%",
            'total_queries': total
        }


_cache_instance = None

def get_query_cache(ttl: int = None) -> QueryCache:
    global _cache_instance
    if _cache_instance is None:
        if ttl is None:
            from config.settings import settings
            ttl = settings.CACHE_TTL
        _cache_instance = QueryCache(ttl=ttl)
    return _cache_instance

