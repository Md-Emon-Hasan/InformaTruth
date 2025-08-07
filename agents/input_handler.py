import newspaper
import fitz
import logging
from typing import Dict
from typing import Any
from config import PipelineConfig

logger = logging.getLogger(__name__)

class InputHandler:
    @staticmethod
    def process(state: Dict[str, Any]) -> Dict[str, Any]:
        input_type = state["input_type"]
        value = state["value"]
        
        try:
            logger.info(f"Processing {input_type} input: {value[:50]}...")
            
            if input_type == 'url':
                article = newspaper.Article(value)
                article.download()
                article.parse()
                text = article.text
            elif input_type == 'pdf':
                with fitz.open(value) as doc:
                    text = "\n".join([page.get_text() for page in doc])
            elif input_type == 'text':
                text = value
            else:
                text = ""
                logger.warning(f"Unsupported input type: {input_type}")
            
            logger.debug(f"Extracted text length: {len(text)} characters")
            return {**state, "text": text}
            
        except Exception as e:
            logger.error(f"Input processing error: {str(e)}")
            return {**state, "error": str(e), "text": ""}