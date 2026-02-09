from app.utils.results import display_results
from unittest.mock import patch


def test_display_results():
    result = {"label": "Real", "confidence": 0.95, "explanation": "Test explanation"}
    with patch("builtins.print") as mock_print:
        display_results(result, "text")
        # Verify it prints something
        assert mock_print.called
