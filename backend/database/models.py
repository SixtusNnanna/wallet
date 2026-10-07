from datetime import datetime, date, UTC
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQL_ENUM,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,

)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.db_types import (
    LoanStatus,
    RepaymentStatus,
    Role,
    LedgerEntryType,
    RepaymentFrequency,
    SchedulePaymentStatus
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
    )
    phone: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
    )
    address: Mapped[str] = mapped_column(String(500))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        SQL_ENUM(
            Role,
            name="role_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=Role.CUSTOMER,
        server_default="customer",
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[UUID] = mapped_column(
            PG_UUID(as_uuid=True),
            primary_key=True,
            default=uuid4,
        )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    principal: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    savings_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    repayment_frequency: Mapped[RepaymentFrequency] = mapped_column(
        SQL_ENUM(
            RepaymentFrequency,
            name="repayment_frequncy_enum",
            values_callable=lambda x: [e.value for e in x]
        ),
        default=RepaymentFrequency.MONTHLY,
        server_default="monthly"
    )
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    term: Mapped[int] = mapped_column(Integer, default=12)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    installment: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[LoanStatus] = mapped_column(
        SQL_ENUM(
            LoanStatus,
            name="loan_status_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=LoanStatus.ACTIVE,
        server_default="active",
    )
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
        )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            default=datetime.now,
        )
    updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            default=datetime.now,
        )

    __table_args__ = (
        CheckConstraint(
            "principal > 0",
            name="ck_loans_principal_postive",
            ),
        CheckConstraint(
            "interest_rate >= 0",
            name="ck_loans_interest_rate_non_negative",
            ),
        CheckConstraint(
            "balance >= 0",
            name="ck_loans_balance_non_negative",
        )
    )


class Repayment(Base):
    __tablename__ = "repayments"
    id: Mapped[UUID] = mapped_column(
            PG_UUID(as_uuid=True),
            primary_key=True,
            default=uuid4,
            )
    loan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("loans.id"),
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    status: Mapped[RepaymentStatus] = mapped_column(
        SQL_ENUM(
            RepaymentStatus,
            name="repayment_status_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=RepaymentStatus.PENDING,
        server_default="pending"
    )
    gateway_reference: Mapped[str] = mapped_column(String(255), unique=True)
    payment_method: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
                DateTime(timezone=True),
                default=datetime.now,
            )
    paid_at: Mapped[datetime | None] = mapped_column(
                DateTime(timezone=True),
                nullable=True
            )
    updated_at: Mapped[datetime] = mapped_column(
                DateTime(timezone=True),
                default=datetime.now,
            )


class RepaymentSchedule(Base):
    __tablename__ = "repayment_schedules"
    id: Mapped[UUID] = mapped_column(
                PG_UUID(as_uuid=True),
                primary_key=True,
                default=uuid4,
                )
    loan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("loans.id"),
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
    )
    installment_number: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00")
    )
    status: Mapped[SchedulePaymentStatus] = mapped_column(
            SQL_ENUM(
                SchedulePaymentStatus,
                name="schedule_payment_status_enum",
                values_callable=lambda x: [e.value for e in x],
            ),
            default=SchedulePaymentStatus.PENDING,
            server_default="pending"
        )

    created_at: Mapped[datetime] = mapped_column(
                DateTime(timezone=True),
                default=datetime.now,
            )

class Ledger(Base):
    __tablename__ = "ledgers"
    id: Mapped[UUID] = mapped_column(
                PG_UUID(as_uuid=True),
                primary_key=True,
                default=uuid4,
                )
    loan_id: Mapped[UUID] = mapped_column(
                PG_UUID(as_uuid=True),
                ForeignKey("loans.id"),
                index=True,
            )
    user_id: Mapped[UUID] = mapped_column(
                    PG_UUID(as_uuid=True),
                    ForeignKey("users.id"),
                    index=True,
                )
    repayment_id: Mapped[UUID] = mapped_column(
                PG_UUID(as_uuid=True),
                ForeignKey("repayments.id"),
                index=True,
                nullable=True
            )

    entry_type: Mapped[LedgerEntryType] = mapped_column(
        SQL_ENUM(
            LedgerEntryType,
            name="ledger_entry_type_enum",
            values_callable=lambda x: [e.value for e in x]
        ),
        default=LedgerEntryType.DISBURSEMENT,
        server_default="disbursement"
    )
    account: Mapped[str] = mapped_column(String(30))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    description: Mapped[str] = mapped_column(Text)
    reference: Mapped[str] = mapped_column(String(255))
    created_by: Mapped[UUID | None] = mapped_column(
                        PG_UUID(as_uuid=True),
                        ForeignKey("users.id"),
                        nullable=True,
                )
    created_at: Mapped[datetime] = mapped_column(
                    DateTime(timezone=True),
                    default=datetime.now,
                )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[UUID] = mapped_column(
                        PG_UUID(as_uuid=True),
                        primary_key=True,
                        default=uuid4,
                        )
    event_id: Mapped[str] = mapped_column(
                        String(255),
                        unique=True
                    )
    event_type: Mapped[str] = mapped_column(String(100))
    gate_way: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[datetime] = mapped_column(
                    DateTime(timezone=True)
                )
    repayment_id: Mapped[UUID] = mapped_column(
                            PG_UUID(as_uuid=True),
                            ForeignKey("repayments.id"),
                            index=True,
                            nullable=True
                        )
    created_at: Mapped[datetime] = mapped_column(
                        DateTime(timezone=True),
                        default=datetime.now,
                    )
