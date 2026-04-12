from src.ml.evaluation.metrics import exact_match


def test_exact_match() -> None:
    assert exact_match("answer", "answer") == 1.0
    assert exact_match("answer", "different") == 0.0
