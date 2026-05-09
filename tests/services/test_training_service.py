import pytest
from fastapi import HTTPException

from src.services.training_service import TrainingService


def test_training_service_rejects_path_traversal() -> None:
    service = TrainingService()
    with pytest.raises(HTTPException) as exc_info:
        service.start_training("../../etc/passwd", "checkpoints/test")

    assert exc_info.value.status_code == 400
