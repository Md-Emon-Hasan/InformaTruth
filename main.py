import sys
from pathlib import Path
import logging
sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import setup_logging
from models.loader import ModelLoader
from models.classifier import Classifier
from graph.builder import PipelineBuilder
from utils.results import display_results

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    logger.info("Starting Fake News Detection Pipeline")
    
    try:
        # Initialize models
        model_loader = ModelLoader()
        model_loader.load_models()
        
        # Create classifier
        classifier = Classifier(
            model_loader.roberta_tokenizer,
            model_loader.roberta_model
        )
        
        # Build pipeline
        pipeline = PipelineBuilder.build_graph(
            classifier,
            model_loader.flan_tokenizer,
            model_loader.flan_model
        )
        
        # Test cases
        test_inputs = [
            {"input_type": "text", "value": "The moon landing was faked in 1969"},
            {"input_type": "url", "value": "https://www.bbc.com/news/articles/cr5rdl1y8ndo"},
            {"input_type": "pdf", "value": "./news/news.pdf"}
        ]
        
        # Process each case
        for case in test_inputs:
            logger.info(f"\nProcessing {case['input_type']} input")
            result = pipeline.invoke(case)
            display_results(result, case["input_type"])
            
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {str(e)}")
        raise
    finally:
        logger.info("Pipeline execution completed")

if __name__ == "__main__":
    main()