from langgraph.graph import StateGraph
from langgraph.graph import END
from agents import InputHandler
from agents import Planner
from agents import FallbackSearch
from agents import Router
from agents import Executor
from .state import AgentState
import logging

logger = logging.getLogger(__name__)

class PipelineBuilder:
    @staticmethod
    def build_graph(classifier, flan_tokenizer, flan_model):
        logger.info("Initializing pipeline graph")
        
        executor = Executor(classifier, flan_tokenizer, flan_model)
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("InputHandler", InputHandler.process)
        graph.add_node("Planner", Planner.decide_flow)
        graph.add_node("FallbackSearch", FallbackSearch.search)
        graph.add_node("Router", Router.route)
        graph.add_node("Executor", executor.execute)
        
        # Set entry point
        graph.set_entry_point("InputHandler")
        
        # Add edges
        graph.add_edge("InputHandler", "Planner")
        graph.add_conditional_edges(
            "Planner",
            lambda s: s["next"],
            {
                "FallbackSearch": "FallbackSearch",
                "Router": "Router"
            }
        )
        graph.add_edge("FallbackSearch", "Router")
        graph.add_edge("Router", "Executor")
        graph.add_edge("Executor", END)
        
        logger.info("Pipeline graph construction complete")
        return graph.compile()