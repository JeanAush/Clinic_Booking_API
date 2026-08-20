"""Health-check endpoints."""

from fastapi import APIRouter, status

router = APIRouter(tags=["health"])


@router.get("/", status_code=status.HTTP_200_OK)
def health_check() -> dict[str, str]:
    """Report that the API process is running."""

    return {"status": "ok"}
