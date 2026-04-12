from pathlib import Path


class LocalPredictor:
    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir

    def predict(self, text: str) -> str:
        return f"[stub prediction from {self.model_dir.name}] {text}"
