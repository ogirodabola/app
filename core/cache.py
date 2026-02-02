import time

_cache = {}

def get_cache(key):
    data = _cache.get(key)
    if not data:
        return None

    value, expires_at = data
    if time.time() > expires_at:
        del _cache[key]
        return None

    return value


def set_cache(key, value, ttl=600):
    _cache[key] = (value, time.time() + ttl)
