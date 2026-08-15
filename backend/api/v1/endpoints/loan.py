from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from backend.api.dependencies import CurrentUserDps, LoanDeps, EmployeeDeps
from backend.api.schemas.loan import LoanCreate, LoanRead
from backend.database.db_types import LoanStatus


router = APIRouter()


@router.get("/me", response_model=LoanRead)
async def get_active_loan(service: LoanDeps, user: CurrentUserDps):
    return await service.get_active_loan_(user_id=user.id)


@router.post("/", response_model=LoanRead)
async def create_loan(
    service: LoanDeps,
    user: EmployeeDeps,
    loan_data: LoanCreate
        ):
    if loan_data.user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot Create Loan for yourself"
        )
    return await service.create_loan(loan_data)

@router.get("/pending", response_model=list[LoanRead])
async def get_pending_loan(
    service: LoanDeps, user: EmployeeDeps, limit: int = 100, offset: int = 0
):
    return await service.loan_pending(limit=limit, skip=offset)


@router.get("/me/history", response_model=list[LoanRead])
async def loan_history(service: LoanDeps, user: CurrentUserDps):
    return await service.get_owners_loan_history(user_id=user.id)

@router.get("/staff", response_model=list[LoanRead])
async def get_all_lones_for_staff(service: LoanDeps, user: EmployeeDeps, status_: LoanStatus, offset: int = 0, limit: int = 100):
    return await service.get_all_loans(status_, limit, offset)


@router.get("/{loan_id}", response_model=LoanRead)
async def get_loan(service: LoanDeps, user: CurrentUserDps, loan_id: UUID):
    return await service.get_loan_by_id(loan_id=loan_id, user_id=user.id)

@router.get("/{loan_id}/staff", response_model=LoanRead)
async def get_any_loan_by_id(service: LoanDeps, user: EmployeeDeps, loan_id: UUID):
    return await service.get_just_any_loan_with_id(loan_id=loan_id)








