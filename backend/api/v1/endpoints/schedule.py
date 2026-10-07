from fastapi import Depends, APIRouter, HTTPException, status
from backend.api.dependencies import ScheduleDeps, CurrentLoanDeps
from backend.api.schemas.schedule import ScheduleRead


router = APIRouter()


@router.get("/user-schedule", status_code=200, response_model=list[ScheduleRead])
async def get_user_schedule(
    schedule_service: ScheduleDeps,
    user_loan_context: CurrentLoanDeps,
):
    schedule_list = await schedule_service.get_user_payment_schedule(
        user_loan_context.user, user_loan_context.loan
    )
    if schedule_list == []:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No Repayment Schedule, you probably don't have a loan"
            )
        )
    return schedule_list


@router.get("/recent_schedule", status_code=200, response_model=list[ScheduleRead])
async def get_recent_payment_schedules(
    schedule_service: ScheduleDeps,
    user_loan_context: CurrentLoanDeps
):
    schedules = (
        await schedule_service.get_next_three_pending_repayment_schedule(
            user_loan_context.user,
            user_loan_context.loan
        )
    )

    if schedules == []:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No Repayment Schedule, you probably don't have a loan"
            ),
        )

    return schedules

