from app.utils.results import display_results
from unittest.mock import patch


def test_display_results():
    result = {"label": "Real", "confidence": 0.95, "explanation": "Test explanation"}
    with patch("builtins.print") as mock_print:
        display_results(result, "text")
        # Verify it prints something
        assert mock_print.called


def test_display_results_shows_fallback_used_notice(capsys):
    result = {
        "label": "Fake",
        "confidence": 0.5,
        "explanation": "x",
        "fallback_used": True,
    }
    display_results(result, "text")
    assert "fallback" in capsys.readouterr().out.lower()


def test_display_results_shows_error(capsys):
    result = {
        "label": "Fake",
        "confidence": 0.5,
        "explanation": "x",
        "error": "boom",
    }
    display_results(result, "text")
    assert "boom" in capsys.readouterr().out
