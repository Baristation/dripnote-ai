from pathlib import Path

from fastapi import HTTPException, status

from src.ml.trainers.sft_trainer import SFTTrainerService


ALLOWED_DATA_ROOT = Path("data").resolve()
ALLOWED_MODELS_ROOT = Path("models").resolve()


def _resolve_safe_path(base: Path, user_input: str) -> Path:
    # 사용자가 넘긴 경로는 지정된 base 아래의 상대 경로만 허용합니다.
    # ../../etc/passwd 같은 path traversal 입력은 resolve 후 base 밖으로 나가므로 차단됩니다.
    candidate = (base / user_input).resolve()
    if not candidate.is_relative_to(base):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path",
        )
    return candidate


class TrainingService:
    def __init__(self) -> None:
        self.trainer = SFTTrainerService()

    def start_training(self, train_path: str, output_dir: str) -> str:
        dataset_path = _resolve_safe_path(ALLOWED_DATA_ROOT, train_path)
        target_dir = _resolve_safe_path(ALLOWED_MODELS_ROOT, output_dir)

        if dataset_path.suffix != ".jsonl":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="train_path must point to a .jsonl file",
            )
        if not dataset_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="train_path does not exist",
            )

        self.trainer.train(dataset_path=dataset_path, output_dir=target_dir)
        return target_dir.name
