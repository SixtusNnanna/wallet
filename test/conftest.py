from decimal import Decimal
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.api.dependencies import (
    get_paystack_client,
    get_current_loan,
    CurrentLoanContext,
    get_repayment_service,
)
from backend.database.base import Base
from backend.database.models import Loan, Repayment, User, Ledger
from backend.database.session import get_session
from backend.main import app
from backend.services.user import pwd_context


TEST_DB_URL = "postgresql+asyncpg://mac@localhost:5432/test_db"


@pytest_asyncio.fixture
async def session():
    test_engine = create_async_engine(TEST_DB_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,

    )
    async with TestSessionLocal() as s:
        yield s

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(session):
    async def override_session():
        yield session
    mock_paystack = AsyncMock()
    mock_paystack.initialize_transaction.return_value = {
        "data": {
            "reference": "test-ref-123",
            "authorization_url": "https://checkout.paystack.com/test-ref-123",
        }
    }

    app.dependency_overrides[get_paystack_client] = lambda: mock_paystack
    app.dependency_overrides[get_session] = override_session

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user(session):
    admin = User(
        full_name="Test Admin",
        email="admin@test.com",
        phone="+2347000000001",
        address="Admin Address",
        password_hash=pwd_context.hash("H@ty1232"),
        role="admin",
        is_verified=True,
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def customer_user(session):
    customer = User(
        full_name="Test Customer",
        email="customer@test.com",
        phone="+2347010000001",
        address="Customer Address",
        password_hash=pwd_context.hash("H@ty1232"),
        role="customer",
        is_verified=True,
    )
    session.add(customer)
    await session.commit()
    await session.refresh(customer)
    return customer


@pytest_asyncio.fixture
async def access_token(client, admin_user):
    response = await client.post(
        "/auth/token", data={
            "username": admin_user.email,
            "password": "H@ty1232"
        })
    assert response.status_code == 200

    token = response.json()["access_token"]
    return f"Bearer {token}"


@pytest_asyncio.fixture
async def access_token_customer(client, customer_user):
    response = await client.post(
        "/auth/token", data={
            "username": customer_user.email,
            "password": "H@ty1232"
        })
    assert response.status_code == 200

    token = response.json()["access_token"]
    return f"Bearer {token}"


@pytest_asyncio.fixture
async def loan(session, customer_user):
    loan = Loan(
        user_id=str(customer_user.id),
        principal=100000,
        balance=136000,
        savings_balance=40800,
        repayment_frequency="daily",
        currency="NGN",
        interest_rate=0.36,
        installment=566.67,
        status="active"
    )
    session.add(loan)
    await session.commit()
    await session.refresh(loan)
    return loan


@pytest_asyncio.fixture
async def paid_off_laon(session, admin_user):
    loan = Loan(
        user_id=str(admin_user.id),
        principal=100000,
        balance=136000,
        savings_balance=40800,
        repayment_frequency="daily",
        currency="NGN",
        interest_rate=0.36,
        installment=566.67,
        status="paid_off"
    )
    session.add(loan)
    await session.commit()
    await session.refresh(loan)
    return loan


@pytest_asyncio.fixture
async def repayment_setup(customer_user, loan):
    async def override_current_loan():
        return CurrentLoanContext(
            loan=loan,
            user=customer_user
        )

    app.dependency_overrides[get_current_loan] = override_current_loan

    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def repayment_user_mismatch(admin_user, loan):
    async def override_current_loan():
        return CurrentLoanContext(
            loan=loan,
            user=admin_user
        )

    app.dependency_overrides[get_current_loan] = override_current_loan

    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def repayment(session, loan, customer_user):
    repayment = Repayment(
        id=uuid4(),
        loan_id=loan.id,
        user_id=customer_user.id,
        amount=Decimal("10000.00"),
        currency="NGN",
        status="pending",
        payment_method="Bank Transfer",
        gateway_reference="test-ref-reconcile",
    )
    session.add(repayment)
    await session.commit()
    yield repayment







