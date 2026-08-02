import time

import config
from app.agents.fallback_search import FallbackSearch


def test_concurrent_search_attempts_run_in_parallel(monkeypatch):
    monkeypatch.setattr(config, "SEARCH_MAX_RETRIES", 3)
    monkeypatch.setattr(config, "SEARCH_TIMEOUT_SECONDS", 5)

    class SlowFailDDGS:
        def __init__(self, *args, **kwargs):
            pass

        def text(self, *args, **kwargs):
            time.sleep(0.3)
            raise Exception("still down")

    monkeypatch.setattr("app.agents.fallback_search.DDGS", SlowFailDDGS)

    start = time.perf_counter()
    result = FallbackSearch.search({"value": "unique concurrency timing query"})
    elapsed = time.perf_counter() - start

    assert result["search_unavailable"] is True
    # 3 sequential 0.3s failures would take ~0.9s; run concurrently they
    # should complete close to a single 0.3s attempt plus overhead.
    assert elapsed < 0.7


def test_first_successful_attempt_wins_even_if_another_fails(monkeypatch):
    monkeypatch.setattr(config, "SEARCH_MAX_RETRIES", 2)
    monkeypatch.setattr(config, "SEARCH_TIMEOUT_SECONDS", 5)

    call_count = {"n": 0}

    class MixedDDGS:
        def __init__(self, *args, **kwargs):
            pass

        def text(self, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise Exception("first attempt down")
            return iter([{"title": "t", "body": "second attempt succeeded"}])

    monkeypatch.setattr("app.agents.fallback_search.DDGS", MixedDDGS)

    result = FallbackSearch.search({"value": "unique mixed outcome query"})

    assert result["text"] == "second attempt succeeded"
    assert result.get("search_unavailable") is not True


def test_slow_branch_times_out_without_hanging_the_request(monkeypatch):
    monkeypatch.setattr(config, "SEARCH_MAX_RETRIES", 1)
    monkeypatch.setattr(config, "SEARCH_TIMEOUT_SECONDS", 0.1)

    class HangingDDGS:
        def __init__(self, *args, **kwargs):
            pass

        def text(self, *args, **kwargs):
            time.sleep(3)
            return iter([{"title": "t", "body": "too late"}])

    monkeypatch.setattr("app.agents.fallback_search.DDGS", HangingDDGS)

    start = time.perf_counter()
    result = FallbackSearch.search({"value": "unique hanging query"})
    elapsed = time.perf_counter() - start

    assert result["search_unavailable"] is True
    # Bounded by the per-branch timeout (SEARCH_TIMEOUT_SECONDS + 2s buffer),
    # not by the branch's real 3s sleep.
    assert elapsed < 2.5
