from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.celery_app import celery_app

router = APIRouter(prefix="/ops")

@router.post("/scan")
def manual_scan(_: None = Depends(get_current_user)):
    try:
        celery_app.send_task("app.tasks.reddit_tasks.scan_reddit")
        return {"enqueued": True}
    except Exception as exc:
        # Return a clear error when broker/result backend is unavailable
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to enqueue scan task: {str(exc)}",
        )



