from fastapi import APIRouter, Depends

from app.adapters.inbound.http.api.v1.routes.reportes_declaracion import router as declaracion_router
from app.adapters.inbound.http.api.v1.routes.reportes_exports import router as exports_router
from app.adapters.inbound.http.api.v1.routes.reportes_summary import router as summary_router
from app.adapters.inbound.http.deps import require_user

router = APIRouter(tags=["reportes"], dependencies=[Depends(require_user)])
router.include_router(summary_router)
router.include_router(declaracion_router)
router.include_router(exports_router)
