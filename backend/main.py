from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.integration.paystack import PaystackClient
from backend.database.session import engine

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from scalar_fastapi import get_scalar_api_reference

from backend.api.v1.base import router
from backend.database.session import create_table
from backend.exceptions import user as user_exception

@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    await create_table()
    app.state.paystack_client = PaystackClient()
    yield
    await app.state.paystack_client.close()
    await engine.dispose()



app = FastAPI(lifespan=lifespan_handler)

app.include_router(router)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    errors = []

    for error in exc.errors():
        errors.append({
            "field": error["loc"][-1],
            "message": error["msg"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "detail": errors
        })


@app.exception_handler(user_exception.UserVerifyEmailError)
def EmailVerificationError(request: Request, exc: user_exception.UserVerifyEmailError):
    return JSONResponse(status_code=403, content={"detail": "Verify Email"})


@app.exception_handler(user_exception.ExistsError)
async def user_exists_handler(request: Request, exc: user_exception.ExistsError):
    # 400 Bad Request: Domin bayanan da aka turo sun riga sun kasance
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": f"{exc.name} Already Exists"},
    )

@app.exception_handler(user_exception.RateLimitException)
async def rate_limit_handler(
    request: Request,
    exc: user_exception.RateLimitException
):
    # 400 Bad Request: Domin bayanan da aka turo sun riga sun kasance
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail":  "You can't make  another request a this moment, try again"
            },
    )

@app.exception_handler(user_exception.NotFoundError)
async def user_not_found_handler(
    request: Request, exc: user_exception.NotFoundError
):
    # 404 Not Found: Domin ba a sami rukunin bayanan ba
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"{exc.name}, Not Found"},
    )


@app.exception_handler(user_exception.InvalidPasswordError)
async def invalid_password_handler(
    request: Request, exc: user_exception.InvalidPasswordError
):
    # 401 Unauthorized: Domin matsalar tantancewa (Authentication) ce
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Kalmar sirri (Password) ba daidai ba ce."},
    )

@app.exception_handler(user_exception.PaymentInitiationError)
async def paymenterrorException(request: Request, exc: user_exception.PaymentInitiationError ):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Could not initiate payment, try again"},
        )

@app.exception_handler(user_exception.InvalidTokenError)
async def invalid_token_handler(
    request: Request, exc: user_exception.InvalidTokenError
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Token ɗinka ba shi da inganci ko ya mutu."},
    )

@app.exception_handler(user_exception.InvalidCodeError)
async def invalid_code_hander(
    request: Request, exc: user_exception.InvalidCodeError
):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": f"{exc}"},
    )


@app.exception_handler(user_exception.PaymentError)
async def payment_exception(request: Request, exc: user_exception.PaymentError):
    return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)}
        )

@app.exception_handler(user_exception.RepaymentAlreadPendingError)
async def repayment_pending_exception(request: Request, exc: user_exception.RepaymentAlreadPendingError):
    return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)}
        )
@app.exception_handler(user_exception.NoActiveLoanError)
async def no_loan_exception(request: Request, exc: user_exception.NoActiveLoanError):
    return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)})
@app.exception_handler(user_exception.IntegrityError)
async def repayment_already_confirmed_exception(request: Request, exc: user_exception.IntegrityError):
    return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)})

@app.exception_handler(user_exception.PaymentAmountMismatchError)
async def payment_amount_exception(
    request: Request,
    exc: user_exception.PaymentAmountMismatchError,
    ):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )

@app.exception_handler(user_exception.BadRequestException)
async def bad_request_exception(
    request: Request,
    exc: user_exception.BadRequestException,
        ):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )

@app.exception_handler(user_exception.RepaymentAmountInsufficent)
async def repayment_amount_exception(
    request: Request,
    exc: user_exception.RepaymentAmountInsufficent,
        ):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.get("/scalars", include_in_schema=False)
async def get_scalar_docs():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title="Scalars API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
