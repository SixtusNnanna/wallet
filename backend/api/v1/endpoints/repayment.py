from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from backend.api.dependencies import CurrentUserDps, EmployeeDeps, RepaymentDps, CurrentLoanDeps
from backend.api.schemas.repayment import RepaymentCreate, RepaymentRead
from backend.database.db_types import RepaymentStatus

router = APIRouter()


@router.post("/initiate", response_model=dict)
async def make_repayment(
    service: RepaymentDps,
    repayment_data: RepaymentCreate,
    current_loan: CurrentLoanDeps
) -> dict:
    return await service.make_payment(
        repayment_data,
        current_loan.user,
        current_loan.loan,
    )


@router.get("/me", response_model=list[RepaymentRead])
async def get_users_repayment(
    
    service: RepaymentDps,
    user: CurrentUserDps,
    limit: int = 100,
    skip: int = 0,
):
    return await service.get_repayments(user.id, limit, skip)


@router.get("/{repayment_id}", response_model=RepaymentRead)
async def get_repayment(
    service: RepaymentDps, user: CurrentUserDps, repayment_id: UUID
):
    return await service.get_repayment(
        user_id=user.id, repayment_id=repayment_id
    )

@router.get("/staff", response_model=list[RepaymentRead])
async def get_repayment_staff(
    service: RepaymentDps,
    user: EmployeeDeps,
    limit: int = 100,
    skip: int = 0,
):
    return await service.get_all_repayment(limit=limit, skip=skip)


@router.get("/{repayment_id}/staff", response_model=RepaymentRead)
async def get_repayment_by_staff(
    service: RepaymentDps, repayment_id: UUID,
    user: EmployeeDeps,
 ):
    return await service.get_repayment_staff(repayment_id=repayment_id)


@router.post("/{repayment_id}/reconcile")
async def reconcile(repayment_id: UUID, service: RepaymentDps, employee: EmployeeDeps):
    return await service.repayment_reconcile(repayment_id)







