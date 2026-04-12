from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.training_service import TrainingService


router = APIRouter(tags=["training"])
training_service = TrainingService()


class TrainRequest(BaseModel):
    train_path: str = Field(..., description="JSONL path for supervised fine-tuning")
    output_dir: str = Field(..., description="Directory where checkpoints will be written")


@router.post("/train")
def train(request: TrainRequest) -> dict[str, str]:
    job = training_service.start_training(request.train_path, request.output_dir)
    return {"status": "started", "job": job}
