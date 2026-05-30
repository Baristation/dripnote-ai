from fastapi.testclient import TestClient

from apps.api.main import app


client = TestClient(app)


def test_product_index_requires_internal_key() -> None:
    response = client.post("/api/rag/index/products")
    assert response.status_code == 403


def test_chat_requires_internal_key() -> None:
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 403


def test_train_requires_internal_key() -> None:
    response = client.post(
        "/api/train",
        json={"train_path": "raw/train.jsonl", "output_dir": "checkpoints/test"},
    )
    assert response.status_code == 403
