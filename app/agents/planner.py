import logging
from typing import Dict
from typing import Any
from config import PipelineConfig

logger = logging.getLogger(__name__)


class Planner:
    @staticmethod
    def decide_flow(state: Dict[str, Any]) -> Dict[str, Any]:
        text = state.get("text", "")

        if len(text.strip()) < PipelineConfig.MIN_TEXT_LENGTH:
            logger.warning(f"Text too short ({len(text)} chars), using fallback")
            return {**state, "next": "FallbackSearch"}

        logger.info("Text sufficient, proceeding to classification")
        return {**state, "next": "Router"}
