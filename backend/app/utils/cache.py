import hashlib
import logging
import threading
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from cachetools import TTLCache

import config

logger = logging.getLogger(__name__)


class _Layer:
    def __init__(self, maxsize: int, ttl: int):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key):
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None

    def set(self, key, value):
        if value is None:
            return
        with self._lock:
            self._cache[key] = value

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self):
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total) if total else 0.0
            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "ttl": self.ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
            }


_url_layer = _Layer(config.URL_CACHE_MAXSIZE, config.URL_CACHE_TTL)
_classify_layer = _Layer(config.CLASSIFY_CACHE_MAXSIZE, config.CLASSIFY_CACHE_TTL)
_search_layer = _Layer(config.SEARCH_CACHE_MAXSIZE, config.SEARCH_CACHE_TTL)

_TRACKING_PREFIXES = ("utm_",)
_TRACKING_PARAMS = {"fbclid", "gclid", "ref", "ref_src"}


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    kept_params = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith(_TRACKING_PREFIXES)
        and k.lower() not in _TRACKING_PARAMS
    ]
    query = urlencode(sorted(kept_params))

    path = parsed.path.rstrip("/") or "/"

    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def hash_text(text: str) -> str:
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached_url_text(url: str):
    if not config.CACHE_ENABLED:
        return None
    return _url_layer.get(normalize_url(url))


def set_cached_url_text(url: str, text: str):
    if not config.CACHE_ENABLED:
        return
    if not text:
        return
    _url_layer.set(normalize_url(url), text)


def get_cached_classification(text: str):
    if not config.CACHE_ENABLED:
        return None
    return _classify_layer.get(hash_text(text))


def set_cached_classification(text: str, result):
    if not config.CACHE_ENABLED:
        return
    if result is None:
        return
    _classify_layer.set(hash_text(text), result)


def get_cached_search(query: str):
    if not config.CACHE_ENABLED:
        return None
    return _search_layer.get(normalize_text(query))


def set_cached_search(query: str, result: str):
    if not config.CACHE_ENABLED:
        return
    if not result:
        return
    _search_layer.set(normalize_text(query), result)


def clear_all_caches():
    _url_layer.clear()
    _classify_layer.clear()
    _search_layer.clear()
    logger.info("All caches cleared")


def cache_stats():
    return {
        "url_cache": _url_layer.stats(),
        "classify_cache": _classify_layer.stats(),
        "search_cache": _search_layer.stats(),
    }
