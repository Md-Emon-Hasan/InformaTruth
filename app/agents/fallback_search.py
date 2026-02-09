from duckduckgo_search import DDGS
import logging
from typing import Dict
from typing import Any
from config import PipelineConfig

logger = logging.getLogger(__name__)


class FallbackSearch:
    @staticmethod
    def search(state: Dict[str, Any]) -> Dict[str, Any]:
        value = state.get("value", PipelineConfig.FALLBACK_SEARCH_QUERY)

        try:
            logger.info(f"Performing fallback search for: {value}")
            results = DDGS().text(value)
            top_result = next(results, None)

            if top_result:
                logger.debug(f"Found fallback result: {top_result['title']}")
                return {**state, "text": top_result["body"], "fallback_used": True}

            logger.warning("No fallback results found")
            return {**state, "text": "No information found", "fallback_used": True}

        except Exception as e:
            logger.error(f"Fallback search failed: {str(e)}")
            return {
                **state,
                "text": "Search failed",
                "fallback_used": True,
                "error": str(e),
            }
