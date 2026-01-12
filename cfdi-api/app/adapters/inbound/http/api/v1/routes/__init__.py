from fastapi import APIRouter
from .home import router as home_router
from .facturas import router as facturas_router
from .retenciones import router as retenciones_router
from .declaraciones import router as declaraciones_router
from .imports import router as imports_router
from .reportes import router as reportes_router

api_router = APIRouter()
api_router.include_router(home_router)
api_router.include_router(facturas_router)
api_router.include_router(retenciones_router)
api_router.include_router(declaraciones_router)
api_router.include_router(imports_router)
api_router.include_router(reportes_router)
