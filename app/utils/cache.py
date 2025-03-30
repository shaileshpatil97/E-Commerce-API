from flask_caching import Cache
from functools import wraps
import hashlib
import json

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
})

def memoize(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create a unique cache key based on function name and arguments
            cache_key = f"{f.__name__}:{hashlib.md5(json.dumps((args, kwargs)).encode()).hexdigest()}"
            
            # Try to get the result from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # If not in cache, execute the function
            result = f(*args, **kwargs)
            
            # Store the result in cache
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        return decorated_function
    return decorator

def clear_cache_for_function(function_name):
    """Clear all cache entries for a specific function."""
    pattern = f"{function_name}:*"
    cache.delete_pattern(pattern)

def clear_all_cache():
    """Clear all cache entries."""
    cache.clear() 