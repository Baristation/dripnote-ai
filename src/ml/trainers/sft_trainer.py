from pathlib import Path

from src.ml.datasets.jsonl_dataset import load_jsonl_dataset
from src.ml.preprocessing.format_supervised import to_instruction_text


class SFTTrainerService:
    def train(self, dataset_path: Path, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        records = load_jsonl_dataset(dataset_path)
        preview_path = output_dir / "training_preview.txt"

        # 현재는 학습 스텁이다.
        # 실제 파인튜닝 전, 데이터가 어떤 형식으로 들어오는지 미리 확인하는 용도로 저장한다.
        preview = "\n\n".join(to_instruction_text(record) for record in records[:10])
        preview_path.write_text(preview, encoding="utf-8")
