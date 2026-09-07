from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.clients import router as clients_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.payments import router as payments_router
from app.api.v1.endpoints.credentials import router as credentials_router
from app.api.v1.endpoints.notes import router as notes_router
from app.api.v1.endpoints.dashboard import (
    router as dashboard_router,
)

router = APIRouter(prefix="/api/v1")


@router.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


router.include_router(auth_router)
router.include_router(projects_router)
router.include_router(clients_router)
router.include_router(tasks_router)
router.include_router(payments_router)
router.include_router(credentials_router)
router.include_router(notes_router)
router.include_router(dashboard_router)
