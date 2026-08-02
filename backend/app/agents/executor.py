import logging
from typing import Dict
from typing import Any
from config import PipelineConfig
from config import MAX_LENGTH
from config import DEVICE

logger = logging.getLogger(__name__)

EXPLANATION_UNAVAILABLE_MESSAGE = (
    "An explanation could not be generated for this result. "
    "The classification above is still valid."
)


class Executor:
    def __init__(self, classifier, flan_tokenizer, flan_model):
        self.classifier = classifier
        self.flan_tokenizer = flan_tokenizer
        self.flan_model = flan_model

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            pred, confidence = self.classifier.classify(state["text"])
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            return {**state, "error": str(e)}

        state.update(
            {"label": "Real" if pred == 0 else "Fake", "confidence": confidence}
        )

        try:
            state["explanation"] = self._generate_explanation(state)
        except Exception as e:
            logger.warning(f"Explanation generation failed, degrading: {str(e)}")
            state["explanation"] = EXPLANATION_UNAVAILABLE_MESSAGE
            state["explanation_unavailable"] = True

        logger.info("Execution completed successfully")
        return state

    def _generate_explanation(self, state):
        prompt = (
            f"Explain why this might be {state['label'].lower()} news in one sentence: "
            f"{state['text'][:500]}"
        )

        inputs = self.flan_tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=MAX_LENGTH
        ).to(DEVICE)

        output_ids = self.flan_model.generate(
            inputs["input_ids"],
            max_new_tokens=PipelineConfig.MAX_EXPLANATION_TOKENS,
            do_sample=False,
        )

        return self.flan_tokenizer.decode(output_ids[0], skip_special_tokens=True)
