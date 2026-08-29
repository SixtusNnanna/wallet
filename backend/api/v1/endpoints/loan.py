from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from backend.api.dependencies import CurrentUserDps, LoanDeps, EmployeeDeps, CurrentLoanDeps
from backend.api.schemas.loan import LoanCreate, LoanRead
from backend.database.redis import cache_data, get_cached_data


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


@router.get("/me/current")
async def current_loan(loan: CurrentLoanDeps):
    return loan.loan


@router.get("/pending", response_model=list[LoanRead])
async def get_pending_loan(
    service: LoanDeps, user: EmployeeDeps, limit: int = 100, offset: int = 0
):
    cache_key = f"pending-loan{limit}{offset}"

    cached = await get_cached_data(cache_key)
    if cached is not None:
        return cached
    loan_data = await service.loan_pending(limit=limit, skip=offset)
    data = [
        LoanRead.model_validate(loan).model_dump(mode="json")
        for loan in loan_data
        ]
    await cache_data(cache_key, data)
    return loan_data


@router.get("/me/history", response_model=list[LoanRead])
async def loan_history(service: LoanDeps, user: CurrentUserDps):
    cache_key = f"user_loans_{user.id}"
    cached = await get_cached_data(cache_key)
    if cached is not None:

        return cached
    user_loan_data = await service.get_owners_loan_history(user_id=user.id)

    data = [
        LoanRead.model_validate(loan).model_dump(mode="json")
        for loan in user_loan_data
        ]
    await cache_data(cache_key, data)
    return user_loan_data


@router.get("/staff", response_model=list[LoanRead])
async def get_all_lones_for_staff(service: LoanDeps, user: EmployeeDeps, status: str = None, offset: int = 0, limit: int = 100):
    cache_key = f"loans-{offset}{limit}"
    cached = await get_cached_data(cache_key)
    if cached is not None:

        return cached
    all_loans = await service.get_all_loans(status, limit, offset)

    data = [LoanRead.model_validate(loan).model_dump() for loan in all_loans]

    await cache_data(cache_key, data)
    return all_loans


@router.get("/{loan_id}", response_model=LoanRead)
async def get_loan(service: LoanDeps, user: CurrentUserDps, loan_id: UUID):
    return await service.get_loan_by_id(loan_id=loan_id, user_id=user.id)


@router.get("/{loan_id}/staff", response_model=LoanRead)
async def get_any_loan_by_id(service: LoanDeps, user: EmployeeDeps, loan_id: UUID):
    return await service.get_just_any_loan_with_id(loan_id=loan_id)








