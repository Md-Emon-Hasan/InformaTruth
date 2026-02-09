import logging
from typing import Dict
from typing import Any

logger = logging.getLogger(__name__)


class Router:
    @staticmethod
    def route(state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Routing to executor")
        return state
