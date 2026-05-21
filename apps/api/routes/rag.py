from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.core.security import require_internal_key
from src.rag.pipelines.product_index_pipeline import ProductIndexPipeline
from src.services.job_service import JobService


router = APIRouter(tags=["rag"])
index_jobs = JobService(namespace="index-jobs")


def _run_product_index_job(job_id: str) -> None:
    index_jobs.mark_running(job_id)
    try:
        count = ProductIndexPipeline().run()
    except Exception as error:
        index_jobs.mark_failed(job_id, error)
        raise
    index_jobs.mark_completed(job_id, count=count)


@router.post("/rag/index/products", dependencies=[Depends(require_internal_key)])
def build_product_index(background_tasks: BackgroundTasks) -> dict[str, str]:
    # 백엔드 MySQL read-only 데이터를 읽어 Qdrant 상품 collection을 갱신합니다.
    # 오래 걸릴 수 있는 embedding 작업이므로 HTTP 요청은 job_id만 반환하고 실제 작업은 background task에서 수행합니다.
    job_id = index_jobs.create_job(prefix="index-products")
    background_tasks.add_task(_run_product_index_job, job_id)
    return {"status": "queued", "job_id": job_id}


@router.get("/rag/index/jobs/{job_id}", dependencies=[Depends(require_internal_key)])
def get_product_index_job(job_id: str) -> dict:
    job = index_jobs.get_status(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job
