from fastapi import APIRouter
from backend.api.v1.endpoints.user import router as user_router
from backend.api.v1.endpoints.loan import router as loan_router


router = APIRouter()

router.include_router(user_router, prefix="/auth", tags=["User"])
router.include_router(loan_router, prefix="/loans", tags=["Loan"])
