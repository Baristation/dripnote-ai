from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.core.security import require_internal_key
from src.services.job_service import JobService
from src.services.training_service import TrainingService


router = APIRouter(tags=["training"])
training_service = TrainingService()
training_jobs = JobService(namespace="training-jobs")


class TrainRequest(BaseModel):
    train_path: str = Field(..., description="JSONL path for supervised fine-tuning")
    output_dir: str = Field(..., description="Directory where checkpoints will be written")


def _run_training_job(job_id: str, request: TrainRequest) -> None:
    training_jobs.mark_running(job_id)
    try:
        output_name = training_service.start_training(request.train_path, request.output_dir)
    except Exception as error:
        training_jobs.mark_failed(job_id, error)
        raise
    training_jobs.mark_completed(job_id, output_dir=output_name)


@router.post("/train", dependencies=[Depends(require_internal_key)])
def train(request: TrainRequest, background_tasks: BackgroundTasks) -> dict[str, str]:
    job_id = training_jobs.create_job(prefix="train")
    background_tasks.add_task(_run_training_job, job_id, request)
    return {"status": "queued", "job_id": job_id}


@router.get("/train/jobs/{job_id}", dependencies=[Depends(require_internal_key)])
def get_training_job(job_id: str) -> dict:
    job = training_jobs.get_status(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job
