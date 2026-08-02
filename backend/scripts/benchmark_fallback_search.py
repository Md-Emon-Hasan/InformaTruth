"""Benchmark: sequential vs. concurrent DuckDuckGo fallback-search retries.

Run with: python scripts/benchmark_fallback_search.py

This intentionally does NOT rely on live DuckDuckGo network timing for the
primary numbers - DDG is rate-limited and network jitter makes repeated
measurements noisy and non-reproducible run-to-run. Instead it simulates a
fixed per-call latency so the concurrency *mechanism* itself (thread pool
fan-out vs. a plain sequential loop) is what gets measured, isolated from
network variance. A best-effort live-network run is also attempted and
reported separately, clearly labelled, if the environment has network
access.

The old sequential-retry loop is reproduced locally here (it no longer
exists in app/agents/fallback_search.py) purely for side-by-side timing.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait as futures_wait

SIMULATED_LATENCY_SECONDS = 0.5
ATTEMPTS = 2
RUNS = 5


def _fake_call_fails():
    time.sleep(SIMULATED_LATENCY_SECONDS)
    raise RuntimeError("simulated ddgs failure")


def _fake_call_succeeds():
    time.sleep(SIMULATED_LATENCY_SECONDS)
    return {"title": "t", "body": "b"}


# --- Old behaviour: sequential retries (reproduced for comparison only) -----


def sequential_retries(call, attempts=ATTEMPTS):
    start = time.perf_counter()
    for _ in range(attempts):
        try:
            result = call()
            if result:
                break
        except RuntimeError:
            continue
    return time.perf_counter() - start


# --- New behaviour: concurrent retries (mirrors fallback_search.py) --------
#
# Uses the same persistent ThreadPoolExecutor + concurrent.futures.wait
# primitive as app/agents/fallback_search.py (not asyncio.gather - see that
# module's comment on why asyncio.run()'s executor-shutdown teardown made
# per-branch timeouts silently block anyway).

_EXECUTOR = ThreadPoolExecutor(max_workers=8)


def concurrent_retries(call, attempts=ATTEMPTS):
    start = time.perf_counter()
    futures = [_EXECUTOR.submit(call) for _ in range(attempts)]
    futures_wait(futures, timeout=SIMULATED_LATENCY_SECONDS + 2)
    return time.perf_counter() - start


def _summarize(label, times):
    avg = sum(times) / len(times)
    formatted = ", ".join(f"{t:.3f}" for t in times)
    print(f"{label}: avg={avg:.3f}s  runs=[{formatted}]")
    return avg


def run_scenario(name, call):
    print(
        f"\n--- Scenario: {name} "
        f"(simulated latency={SIMULATED_LATENCY_SECONDS}s, "
        f"attempts={ATTEMPTS}, runs={RUNS}) ---"
    )
    seq_times = [sequential_retries(call) for _ in range(RUNS)]
    conc_times = [concurrent_retries(call) for _ in range(RUNS)]
    seq_avg = _summarize("Sequential (old)", seq_times)
    conc_avg = _summarize("Concurrent (new)", conc_times)
    print(f"Speedup: {seq_avg / conc_avg:.2f}x")


def try_live_network_run():
    print("\n--- Best-effort live DuckDuckGo network run ---")
    try:
        from duckduckgo_search import DDGS

        def live_call():
            results = DDGS(timeout=8).text("latest technology news")
            top = (
                next(results, None)
                if hasattr(results, "__next__")
                else (results[0] if results else None)
            )
            if not top:
                raise RuntimeError("no results")
            return top

        seq_times = [sequential_retries(live_call) for _ in range(3)]
        conc_times = [concurrent_retries(live_call) for _ in range(3)]
        seq_avg = _summarize("Sequential (old), live network", seq_times)
        conc_avg = _summarize("Concurrent (new), live network", conc_times)
        print(f"Speedup: {seq_avg / conc_avg:.2f}x")
    except Exception as e:
        print(f"Live network run skipped/failed: {e}")


if __name__ == "__main__":
    run_scenario("every attempt fails (worst case - the retry path)", _fake_call_fails)
    run_scenario("every attempt succeeds immediately (best case)", _fake_call_succeeds)
    try_live_network_run()
