import time

import config
from app.utils import cache as cache_mod
from app.utils.cache import (
    cache_stats,
    clear_all_caches,
    get_cached_classification,
    get_cached_search,
    get_cached_url_text,
    normalize_text,
    normalize_url,
    set_cached_classification,
    set_cached_search,
    set_cached_url_text,
)


def test_url_cache_hit_and_miss():
    assert get_cached_url_text("http://example.com/a") is None
    set_cached_url_text("http://example.com/a", "article text")
    assert get_cached_url_text("http://example.com/a") == "article text"


def test_url_normalization_maps_equivalent_urls():
    set_cached_url_text("HTTP://Example.com/Path/?utm_source=x&b=2", "shared text")
    assert get_cached_url_text("http://example.com/Path?b=2") == "shared text"
    assert get_cached_url_text("http://example.com/Path/?utm_source=y&b=2") == (
        "shared text"
    )


def test_text_normalization_maps_equivalent_text():
    set_cached_classification("hello   world", (0, 0.9))
    assert get_cached_classification("hello world") == (0, 0.9)
    assert get_cached_classification("  hello\nworld  ") == (0, 0.9)


def test_classify_cache_avoids_rewrapped_call():
    calls = {"n": 0}

    def classify(text):
        calls["n"] += 1
        cached = get_cached_classification(text)
        if cached is not None:
            return cached
        result = (1, 0.5)
        set_cached_classification(text, result)
        return result

    assert classify("some article") == (1, 0.5)
    assert classify("some article") == (1, 0.5)
    assert calls["n"] == 2  # called twice, but only computed once (cache hit path)
    assert get_cached_classification("some article") == (1, 0.5)


def test_search_cache_hit_and_miss():
    assert get_cached_search("who won") is None
    set_cached_search("who won", "the answer")
    assert get_cached_search("who won") == "the answer"


def test_ttl_expiry_misses():
    layer = cache_mod._Layer(maxsize=10, ttl=0.05)
    layer.set("k", "v")
    assert layer.get("k") == "v"
    time.sleep(0.1)
    assert layer.get("k") is None


def test_failures_and_degraded_results_never_cached():
    set_cached_classification("bad text", None)
    assert get_cached_classification("bad text") is None

    set_cached_url_text("http://example.com/empty", "")
    assert get_cached_url_text("http://example.com/empty") is None

    set_cached_search("empty query", "")
    assert get_cached_search("empty query") is None


def test_clear_all_caches_and_stats():
    set_cached_url_text("http://example.com/z", "z text")
    set_cached_classification("z text", (0, 0.1))
    set_cached_search("z query", "z result")

    stats = cache_stats()
    assert stats["url_cache"]["size"] >= 1
    assert stats["classify_cache"]["size"] >= 1
    assert stats["search_cache"]["size"] >= 1
    for layer_stats in stats.values():
        assert set(layer_stats.keys()) == {
            "size",
            "maxsize",
            "ttl",
            "hits",
            "misses",
            "hit_rate",
        }

    clear_all_caches()
    stats_after = cache_stats()
    assert stats_after["url_cache"]["size"] == 0
    assert stats_after["classify_cache"]["size"] == 0
    assert stats_after["search_cache"]["size"] == 0


def test_cache_enabled_false_bypasses_all_layers(monkeypatch):
    monkeypatch.setattr(config, "CACHE_ENABLED", False)
    set_cached_url_text("http://example.com/off", "text")
    assert get_cached_url_text("http://example.com/off") is None

    set_cached_classification("off text", (0, 0.5))
    assert get_cached_classification("off text") is None

    set_cached_search("off query", "off result")
    assert get_cached_search("off query") is None


def test_normalize_helpers():
    assert normalize_text("  a   b  ") == "a b"
    assert normalize_url("HTTP://A.com/x/") == normalize_url("http://a.com/x")
