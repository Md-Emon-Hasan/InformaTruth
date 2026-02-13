from app.graph.builder import PipelineBuilder
from unittest.mock import MagicMock


def test_pipeline_builder_structure():
    mock_classifier = MagicMock()
    mock_tok = MagicMock()
    mock_model = MagicMock()

    pipeline = PipelineBuilder.build_graph(mock_classifier, mock_tok, mock_model)
    assert pipeline is not None
    # Check if we can compile and it has nodes
    assert hasattr(pipeline, "invoke")
