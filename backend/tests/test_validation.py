import base64
import socket
from unittest.mock import patch

import pytest

import config
from app.utils.validation import (
    ContentValidationError,
    validate_and_extract_pdf,
    validate_text,
    validate_url,
)

# Text


def test_validate_text_rejects_whitespace_only():
    with pytest.raises(ContentValidationError):
        validate_text("    \n\t  ")


def test_validate_text_rejects_too_short(monkeypatch):
    monkeypatch.setattr(config, "MIN_TEXT_CHARS", 20)
    with pytest.raises(ContentValidationError):
        validate_text("too short")


def test_validate_text_rejects_too_long(monkeypatch):
    monkeypatch.setattr(config, "MAX_TEXT_CHARS", 10)
    with pytest.raises(ContentValidationError):
        validate_text("this text is definitely too long")


def test_validate_text_rejects_non_alphabetic():
    with pytest.raises(ContentValidationError):
        validate_text("1234567890 !@#$%^&*()")


def test_validate_text_accepts_valid_text():
    assert validate_text("This is perfectly fine article text.")


# URL


def test_validate_url_rejects_file_scheme():
    with pytest.raises(ContentValidationError):
        validate_url("file:///etc/passwd")


def test_validate_url_rejects_ftp_scheme():
    with pytest.raises(ContentValidationError):
        validate_url("ftp://example.com/file")


def test_validate_url_rejects_data_scheme():
    with pytest.raises(ContentValidationError):
        validate_url("data:text/plain;base64,aGVsbG8=")


@patch("socket.gethostbyname", return_value="93.184.216.34")
def test_validate_url_accepts_http_and_https(mock_dns):
    assert validate_url("http://example.com") == "http://example.com"
    assert validate_url("https://example.com") == "https://example.com"


@patch("socket.gethostbyname", return_value="127.0.0.1")
def test_validate_url_rejects_loopback(mock_dns):
    with pytest.raises(ContentValidationError):
        validate_url("http://localhost:8000")


@patch("socket.gethostbyname", return_value="10.0.0.5")
def test_validate_url_rejects_private(mock_dns):
    with pytest.raises(ContentValidationError):
        validate_url("http://internal.local")


@patch("socket.gethostbyname", return_value="169.254.169.254")
def test_validate_url_rejects_link_local(mock_dns):
    with pytest.raises(ContentValidationError):
        validate_url("http://169.254.169.254/")


def test_validate_url_rejects_missing_hostname():
    with pytest.raises(ContentValidationError, match="hostname"):
        validate_url("http://")


@patch("socket.gethostbyname", side_effect=socket.gaierror("no such host"))
def test_validate_url_rejects_unresolvable_host(mock_dns):
    with pytest.raises(ContentValidationError, match="Could not resolve host"):
        validate_url("http://this-does-not-resolve.example")


# PDF


def _fake_pdf_bytes(page_texts=("hello world",)) -> bytes:
    import fitz

    doc = fitz.open()
    for text in page_texts:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    raw = doc.tobytes()
    doc.close()
    return raw


def test_validate_pdf_oversized_rejected_before_parsing(monkeypatch):
    monkeypatch.setattr(config, "MAX_PDF_BYTES", 10)
    raw = _fake_pdf_bytes()
    with pytest.raises(ContentValidationError, match="size"):
        validate_and_extract_pdf(raw)


def test_validate_pdf_too_many_pages_rejected(monkeypatch):
    monkeypatch.setattr(config, "MAX_PDF_PAGES", 1)
    raw = _fake_pdf_bytes(page_texts=("page one", "page two"))
    with pytest.raises(ContentValidationError, match="pages"):
        validate_and_extract_pdf(raw)


def test_validate_pdf_rejects_non_pdf_bytes():
    with pytest.raises(ContentValidationError):
        validate_and_extract_pdf(b"this is not a pdf file")


def test_validate_pdf_rejects_corrupt_pdf_that_fitz_cannot_open():
    # Passes the "%PDF" magic-byte check but is not a real PDF stream.
    raw = b"%PDF-1.4\ncorrupted, not an actual pdf structure"
    with pytest.raises(ContentValidationError, match="Could not open PDF"):
        validate_and_extract_pdf(raw)


def test_validate_pdf_rejects_no_extractable_text():
    import fitz

    doc = fitz.open()
    doc.new_page()  # blank page, no text -> simulates a scanned/image PDF
    raw = doc.tobytes()
    doc.close()

    with pytest.raises(ContentValidationError, match="OCR"):
        validate_and_extract_pdf(raw)


def test_validate_pdf_accepts_valid_pdf_with_text():
    raw = _fake_pdf_bytes(page_texts=("Some real extractable article text.",))
    text = validate_and_extract_pdf(raw)
    assert "Some real extractable article text." in text


def test_base64_roundtrip_is_accepted():
    raw = _fake_pdf_bytes(page_texts=("Encoded content here.",))
    encoded = base64.b64encode(raw).decode()
    decoded = base64.b64decode(encoded, validate=True)
    text = validate_and_extract_pdf(decoded)
    assert "Encoded content here." in text
