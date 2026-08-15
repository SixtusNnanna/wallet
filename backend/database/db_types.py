from enum import Enum


class Role(Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    STAFF = "staf"


class LoanStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAIDOFF = "paid_off"
    DEFAULTED = "defaulted"
    WRIITENOFF = "written_off"


class RepaymentFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RepaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LedgerEntryType(Enum):
    DISBURSEMENT = "disbursement"
    REPAYMENT = "repayment"
    INTEREST_ACCRUAL = "interest_accrual"
    FEE = "fee"
    ADJUSTMENT = "adjustment"
    WRITE_OFF = "write_off"


class TransactionStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

