from pathlib import Path

from src.ml.trainers.sft_trainer import SFTTrainerService


class TrainingService:
    def __init__(self) -> None:
        self.trainer = SFTTrainerService()

    def start_training(self, train_path: str, output_dir: str) -> str:
        dataset_path = Path(train_path)
        target_dir = Path(output_dir)
        self.trainer.train(dataset_path=dataset_path, output_dir=target_dir)
        return target_dir.name
