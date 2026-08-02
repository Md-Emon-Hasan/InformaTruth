import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait as futures_wait
from typing import Any, Dict

from duckduckgo_search import DDGS

import config
from app.utils.cache import get_cached_search, set_cached_search
from config import PipelineConfig

logger = logging.getLogger(__name__)

# Persistent pool, reused across requests. Using concurrent.futures directly
# instead of asyncio here: asyncio.run() waits for abandoned executor work on
# shutdown, which breaks a per-branch timeout - plain wait(timeout=...) doesn't.
_SEARCH_EXECUTOR = ThreadPoolExecutor(
    max_workers=8, thread_name_prefix="fallback-search"
)


def _run_single_query(query: str, timeout: float):
    """One blocking DDGS call, run inside a worker thread."""
    results = DDGS(timeout=timeout).text(query)
    if hasattr(results, "__next__"):
        return next(results, None)
    return results[0] if results else None


def _run_queries_concurrently(query: str, attempts: int, timeout: float):
    """Fan out `attempts` DDGS calls and bound total wait time."""
    futures = [
        _SEARCH_EXECUTOR.submit(_run_single_query, query, timeout)
        for _ in range(attempts)
    ]
    deadline = timeout + 2
    done, pending = futures_wait(futures, timeout=deadline)

    outcomes = []
    for future in done:
        try:
            outcomes.append(future.result())
        except Exception as e:
            outcomes.append(e)
    for _future in pending:
        outcomes.append(TimeoutError(f"search attempt timed out after {deadline}s"))
    return outcomes


class FallbackSearch:
    @staticmethod
    def search(state: Dict[str, Any]) -> Dict[str, Any]:
        value = state.get("value", PipelineConfig.FALLBACK_SEARCH_QUERY)

        cached_text = get_cached_search(value)
        if cached_text is not None:
            logger.info("Search cache hit, skipping DuckDuckGo call")
            return {**state, "text": cached_text, "fallback_used": True}

        attempts = max(config.SEARCH_MAX_RETRIES, 1)
        logger.info(
            f"Performing {attempts} concurrent fallback search attempt(s) for: {value}"
        )

        try:
            outcomes = _run_queries_concurrently(
                value, attempts, config.SEARCH_TIMEOUT_SECONDS
            )
        except Exception as e:
            # Fan-out setup itself failing (not an individual branch) -
            # degrade the same way a fully-failed search would.
            logger.error(f"Fallback search failed after retries: {str(e)}")
            return {
                **state,
                "text": "Search failed",
                "fallback_used": True,
                "search_unavailable": True,
                "error": str(e),
            }

        top_result = None
        last_error = None
        for outcome in outcomes:
            if isinstance(outcome, Exception):
                last_error = outcome
                logger.warning(f"Fallback search attempt failed: {str(outcome)}")
                continue
            if outcome:
                top_result = outcome
                break

        if top_result:
            logger.debug(f"Found fallback result: {top_result['title']}")
            text = top_result["body"]
            set_cached_search(value, text)
            return {**state, "text": text, "fallback_used": True}

        if last_error is not None:
            logger.error(f"Fallback search failed after retries: {str(last_error)}")
            return {
                **state,
                "text": "Search failed",
                "fallback_used": True,
                "search_unavailable": True,
                "error": str(last_error),
            }

        logger.warning("No fallback results found")
        return {
            **state,
            "text": "No information found",
            "fallback_used": True,
            "search_unavailable": True,
        }
