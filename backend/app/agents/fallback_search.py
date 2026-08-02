from duckduckgo_search import DDGS
import logging
from typing import Dict
from typing import Any
from config import PipelineConfig
import config
from app.utils.cache import get_cached_search, set_cached_search

logger = logging.getLogger(__name__)


class FallbackSearch:
    @staticmethod
    def search(state: Dict[str, Any]) -> Dict[str, Any]:
        value = state.get("value", PipelineConfig.FALLBACK_SEARCH_QUERY)

        cached_text = get_cached_search(value)
        if cached_text is not None:
            logger.info("Search cache hit, skipping DuckDuckGo call")
            return {**state, "text": cached_text, "fallback_used": True}

        last_error = None
        for attempt in range(1, config.SEARCH_MAX_RETRIES + 1):
            try:
                logger.info(
                    f"Performing fallback search for: {value} (attempt {attempt})"
                )
                results = DDGS(timeout=config.SEARCH_TIMEOUT_SECONDS).text(value)
                if hasattr(results, "__next__"):
                    top_result = next(results, None)
                else:
                    top_result = results[0] if results else None

                if top_result:
                    logger.debug(f"Found fallback result: {top_result['title']}")
                    text = top_result["body"]
                    set_cached_search(value, text)
                    return {**state, "text": text, "fallback_used": True}

                logger.warning("No fallback results found")
                return {
                    **state,
                    "text": "No information found",
                    "fallback_used": True,
                    "search_unavailable": True,
                }

            except Exception as e:
                last_error = e
                logger.warning(f"Fallback search attempt {attempt} failed: {str(e)}")

        logger.error(f"Fallback search failed after retries: {str(last_error)}")
        return {
            **state,
            "text": "Search failed",
            "fallback_used": True,
            "search_unavailable": True,
            "error": str(last_error),
        }
