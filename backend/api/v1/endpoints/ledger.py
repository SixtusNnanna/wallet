from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from backend.api.dependencies import LedgerDeps, CurrentUserDps, EmployeeDeps
from backend.api.schemas.ledger import LedgerRead
from backend.database.db_types import LedgerEntryType

router = APIRouter()


@router.get("/summary", status_code=200)
async def balance_summary(services: LedgerDeps,  user: CurrentUserDps):
    return await services.get_ledger_summary(
        user.id
    )


@router.get("/", status_code=200, response_model=list[LedgerRead])
async def get_user_ledger(
    user: CurrentUserDps,
    service: LedgerDeps,
    loan_id: UUID | None = None,
    repayment_id: UUID | None = None,
    entry_type: LedgerEntryType | None = None,
    account: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    skip: int = 0,
):
    user_legders = await service.get_user_ledger(
        user_id=user.id,
        loan_id=loan_id,
        repayment_id=repayment_id,
        entry_type=entry_type,
        account=account,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        skip=skip
    )

    if not user_legders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There no ledger associated with you search"
        )
    return user_legders


@router.get("/users", status_code=200, response_model=list[LedgerRead])
async def get_users_ledgers(
        user: EmployeeDeps,
        service: LedgerDeps,
        user_id: UUID | None = None,
        loan_id: UUID | None = None,
        repayment_id: UUID | None = None,
        entry_type: LedgerEntryType | None = None,
        account: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        skip: int = 0,
):
    users_legder = await service.get_user_ledger(
            user_id=user_id,
            loan_id=loan_id,
            repayment_id=repayment_id,
            entry_type=entry_type,
            account=account,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            skip=skip
        )
    if not users_legder:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There no ledger associated with you search"
            )
    return users_legder


@router.get("/{ledger_id}", status_code=status.HTTP_200_OK, response_model=LedgerRead)
async def get_user_ledger_by_id(
    ledger_id: UUID,
    user: CurrentUserDps,
    service: LedgerDeps
):
    result = await service.get_single_user_legder(
        user_id=user.id, ledger_id=ledger_id)
    if result is None:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ledger not found"
                    )
    return result


@router.get(
        "/{ledger_id}/staff",
        status_code=status.HTTP_200_OK,
        response_model=LedgerRead,
        )
async def get_users_ledger_by_id(
    ledger_id: UUID,
    user: EmployeeDeps,
    service: LedgerDeps
):
    result = await service.get_single_legder(
       ledger_id=ledger_id)
    if result is None:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ledger not found"
                    )
    return result


