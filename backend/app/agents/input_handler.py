import base64
import binascii
import logging
from typing import Dict
from typing import Any

import newspaper
import fitz

import config
from app.utils.cache import get_cached_url_text, set_cached_url_text
from app.utils.validation import ContentValidationError, validate_and_extract_pdf
from app.utils.validation import validate_url

logger = logging.getLogger(__name__)


def _decode_pdf_payload(value: str):
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None


class InputHandler:
    @staticmethod
    def process(state: Dict[str, Any]) -> Dict[str, Any]:
        input_type = state["input_type"]
        value = state["value"]

        try:
            logger.info(f"Processing {input_type} input: {value[:50]}...")

            if input_type == "url":
                text = InputHandler._process_url(value)
            elif input_type == "pdf":
                text = InputHandler._process_pdf(value)
            elif input_type == "text":
                text = value
            else:
                text = ""
                logger.warning(f"Unsupported input type: {input_type}")

            logger.debug(f"Extracted text length: {len(text)} characters")
            return {**state, "text": text}

        except ContentValidationError:
            raise
        except Exception as e:
            logger.error(f"Input processing error: {str(e)}")
            return {**state, "error": str(e), "text": ""}

    @staticmethod
    def _process_url(value: str) -> str:
        validated_url = validate_url(value)

        cached_text = get_cached_url_text(validated_url)
        if cached_text is not None:
            logger.info("URL cache hit, skipping Newspaper3k fetch")
            return cached_text

        article = newspaper.Article(
            validated_url,
            fetch_images=False,
            request_timeout=config.HTTP_TIMEOUT_SECONDS,
        )
        article.download()
        article.parse()
        text = article.text

        if len(text.strip()) < config.MIN_URL_TEXT_CHARS:
            raise ContentValidationError(
                "Could not extract enough text from this URL. "
                "Please paste the article text directly instead."
            )

        set_cached_url_text(validated_url, text)
        return text

    @staticmethod
    def _process_pdf(value: str) -> str:
        raw_bytes = _decode_pdf_payload(value)
        if raw_bytes is not None:
            return validate_and_extract_pdf(raw_bytes)

        with fitz.open(value) as doc:
            text = "\n".join([page.get_text() for page in doc])
        return text
