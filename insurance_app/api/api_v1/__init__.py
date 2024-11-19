from fastapi import APIRouter

from .rates.views import router as rates_router


router = APIRouter(prefix="/v1")


router.include_router(rates_router, prefix="/rates")
