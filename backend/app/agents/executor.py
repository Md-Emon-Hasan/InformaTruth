import logging
from typing import Dict
from typing import Any
from config import PipelineConfig
from config import MAX_LENGTH
from config import DEVICE
import config
from app.utils.guardrails import check_output
from app.utils.hallucination import assess_hallucination_risk, self_consistency

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
            raw_explanation = self._generate_explanation(state)
            output_check = check_output(raw_explanation, state.get("text", ""))

            existing_violations = state.get("guardrail_violations") or []
            state["guardrail_violations"] = (
                existing_violations + output_check["violations"]
            )

            if not output_check["sanitised_text"].strip():
                # Nothing safe survived sanitisation (e.g. the output was
                # empty/degenerate) - degrade like any other explanation
                # failure rather than returning an empty string.
                logger.warning(
                    "Explanation failed output guardrails, degrading: "
                    f"{output_check['violations']}"
                )
                state["explanation"] = EXPLANATION_UNAVAILABLE_MESSAGE
                state["explanation_unavailable"] = True
            else:
                state["explanation"] = output_check["sanitised_text"]
        except Exception as e:
            logger.warning(f"Explanation generation failed, degrading: {str(e)}")
            state["explanation"] = EXPLANATION_UNAVAILABLE_MESSAGE
            state["explanation_unavailable"] = True

        state["hallucination"] = self._assess_hallucination(state)

        logger.info("Execution completed successfully")
        return state

    def _build_prompt(self, state):
        return (
            f"Explain why this might be {state['label'].lower()} news in one sentence: "
            f"{state['text'][:500]}"
        )

    def _generate_explanation(self, state):
        prompt = self._build_prompt(state)

        inputs = self.flan_tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=MAX_LENGTH
        ).to(DEVICE)

        output_ids = self.flan_model.generate(
            inputs["input_ids"],
            max_new_tokens=PipelineConfig.MAX_EXPLANATION_TOKENS,
            do_sample=False,
        )

        return self.flan_tokenizer.decode(output_ids[0], skip_special_tokens=True)

    def _assess_hallucination(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Never raises. Skipped if the explanation itself was degraded."""
        if state.get("explanation_unavailable"):
            return {
                "hallucination_risk": "unknown",
                "reasons": ["explanation_unavailable"],
            }

        try:
            resample_result = None
            if config.HALLUCINATION_SELF_CONSISTENCY_ENABLED:
                try:
                    resample_result = self_consistency(
                        self.flan_tokenizer,
                        self.flan_model,
                        self._build_prompt(state),
                        n_samples=config.HALLUCINATION_SELF_CONSISTENCY_SAMPLES,
                    )
                except Exception as e:
                    logger.warning(
                        f"Self-consistency resampling failed, skipping signal: {e}"
                    )

            return assess_hallucination_risk(
                state["label"],
                state["explanation"],
                state.get("text", ""),
                self_consistency_result=resample_result,
            )
        except Exception as e:
            logger.warning(f"Hallucination assessment failed, skipping: {e}")
            return {"hallucination_risk": "unknown", "reasons": ["assessment_failed"]}
