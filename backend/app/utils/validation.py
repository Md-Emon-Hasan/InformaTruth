import ipaddress
import logging
import socket
from urllib.parse import urlparse

import fitz

import config

logger = logging.getLogger(__name__)


class ContentValidationError(ValueError):
    pass


def validate_text(text: str) -> str:
    if text is None or not text.strip():
        raise ContentValidationError("Text input cannot be empty or whitespace-only.")

    stripped = text.strip()

    if len(stripped) < config.MIN_TEXT_CHARS:
        raise ContentValidationError(
            f"Text is too short ({len(stripped)} chars). "
            f"Minimum is {config.MIN_TEXT_CHARS} characters."
        )

    if len(stripped) > config.MAX_TEXT_CHARS:
        raise ContentValidationError(
            f"Text is too long ({len(stripped)} chars). "
            f"Maximum is {config.MAX_TEXT_CHARS} characters."
        )

    if not any(ch.isalpha() for ch in stripped):
        raise ContentValidationError(
            "Text must contain at least some alphabetic characters."
        )

    return text


def validate_url(url: str) -> str:
    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise ContentValidationError("Only http and https URLs are supported.")

    if not parsed.hostname:
        raise ContentValidationError("URL is missing a hostname.")

    try:
        resolved_ip = socket.gethostbyname(parsed.hostname)
    except socket.gaierror as e:
        raise ContentValidationError(f"Could not resolve host: {e}")

    ip = ipaddress.ip_address(resolved_ip)
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
    ):
        raise ContentValidationError(
            "This URL points to an internal address and cannot be fetched."
        )

    return url


def validate_and_extract_pdf(raw: bytes) -> str:
    if len(raw) > config.MAX_PDF_BYTES:
        raise ContentValidationError(
            f"PDF exceeds the maximum allowed size of {config.MAX_PDF_BYTES} bytes."
        )

    if not raw.startswith(b"%PDF"):
        raise ContentValidationError("The uploaded file is not a valid PDF.")

    try:
        doc = fitz.open(stream=raw, filetype="pdf")
    except Exception as e:
        raise ContentValidationError(f"Could not open PDF: {e}")

    try:
        page_count = doc.page_count
        if isinstance(page_count, int) and page_count > config.MAX_PDF_PAGES:
            raise ContentValidationError(
                f"PDF has too many pages ({page_count}). "
                f"Maximum is {config.MAX_PDF_PAGES} pages."
            )
        text = "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()

    if not text.strip():
        raise ContentValidationError(
            "No extractable text found in this PDF. Scanned/image-based "
            "PDFs are not supported (OCR is not performed)."
        )

    return text[: config.MAX_TEXT_CHARS]
