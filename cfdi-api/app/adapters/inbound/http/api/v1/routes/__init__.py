from fastapi import APIRouter
from .home import router as home_router
from .facturas import router as facturas_router
from .retenciones import router as retenciones_router
from .declaraciones import router as declaraciones_router
from .imports import router as imports_router
from .reportes import router as reportes_router
from .platform_rfcs import router as platform_rfcs_router
from .rfc_phones import router as rfc_phones_router
from .sat import router as sat_router
from .sat_descargas import router as sat_descargas_router
from .user_rfcs import router as user_rfcs_router
from .auth import router as auth_router
from .users import router as users_router
from .declaracion_config import router as declaracion_config_router
from .deducciones import router as deducciones_router

api_router = APIRouter()
api_router.include_router(home_router)
api_router.include_router(facturas_router)
api_router.include_router(retenciones_router)
api_router.include_router(declaraciones_router)
api_router.include_router(imports_router)
api_router.include_router(reportes_router)
api_router.include_router(platform_rfcs_router)
api_router.include_router(rfc_phones_router)
api_router.include_router(sat_router)
api_router.include_router(sat_descargas_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(user_rfcs_router)
api_router.include_router(declaracion_config_router)
api_router.include_router(deducciones_router)
