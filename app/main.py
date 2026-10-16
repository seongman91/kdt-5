from __future__ import annotations

import json
import os
import secrets
import tempfile
import uuid
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
from pathlib import Path
from threading import RLock
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator

from classroom_data import add_classroom_records

APP_TITLE = "Unified Banking + HR Tool APIs (JSON-backed)"
APP_VERSION = "2.0.0"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("APP_DATA_DIR", BASE_DIR / "data"))
HR_JSON_PATH = Path(os.getenv("HR_JSON_PATH", DATA_DIR / "hr_users.json"))
BANK_JSON_PATH = Path(os.getenv("BANK_JSON_PATH", DATA_DIR / "bank_data.json"))
# Protect the entire read/modify/write operation within ONE server process.
DATA_LOCK = RLock()
TRAINING_API_KEY = os.getenv("TRAINING_API_KEY", "")
TRAINING_STUDENTS = int(os.getenv("TRAINING_STUDENTS", "0"))
training_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_training_key(
    request: Request, key: Optional[str] = Security(training_key_header)
) -> None:
    if request.url.path == "/health" or not TRAINING_API_KEY:
        return
    if not key or not secrets.compare_digest(key, TRAINING_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


def serialized_write(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        with DATA_LOCK:
            return function(*args, **kwargs)
    return wrapper

TELLER_USERNAME = os.getenv("TELLER_USERNAME", "teller")
TELLER_PASSWORD = os.getenv("TELLER_PASSWORD", "teller123")

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    dependencies=[Depends(require_training_key)],
    description=(
        "Single FastAPI server hosting both banking APIs and HR automation APIs, "
        "with JSON files as the backing store for easy demos and debugging."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Seed data
# -------------------------------------------------------------------
DEFAULT_HR_USERS: dict[str, dict[str, Any]] = {
    "장원영": {
        "user_id": "EMP-1001",
        "name": "장원영",
        "title": "AI Engineer",
        "address": "서울특별시 강남구 테헤란로 101",
        "time_off_balance": 15,
    },
    "카리나": {
        "user_id": "EMP-1002",
        "name": "카리나",
        "title": "Data Engineer",
        "address": "서울특별시 서초구 서초대로 202",
        "time_off_balance": 7,
    },
    "안유진": {
        "user_id": "EMP-1003",
        "name": "안유진",
        "title": "HR Specialist",
        "address": "서울특별시 송파구 올림픽로 303",
        "time_off_balance": 18,
    },
    "민지": {
        "user_id": "EMP-1004",
        "name": "민지",
        "title": "Product Manager",
        "address": "서울특별시 마포구 월드컵북로 404",
        "time_off_balance": 10,
    },
    "해린": {
        "user_id": "EMP-1005",
        "name": "해린",
        "title": "Software Engineer",
        "address": "서울특별시 영등포구 국제금융로 505",
        "time_off_balance": 20,
    },
    "지민": {
        "user_id": "EMP-1006",
        "name": "지민",
        "title": "Senior AI Engineer",
        "address": "경기도 성남시 분당구 판교역로 606",
        "time_off_balance": 14,
    },
    "정국": {
        "user_id": "EMP-1007",
        "name": "정국",
        "title": "Platform Engineer",
        "address": "서울특별시 강서구 마곡중앙로 707",
        "time_off_balance": 11,
    },
    "차은우": {
        "user_id": "EMP-1008",
        "name": "차은우",
        "title": "UX Designer",
        "address": "서울특별시 용산구 한강대로 808",
        "time_off_balance": 16,
    },
}

DEFAULT_BANK_DATA: dict[str, Any] = {
    "accounts": {
        "DE89320895326389021994": {
            "account_id": "ACC-2001",
            "iban": "DE89320895326389021994",
            "customer_name": "장원영",
            "current_balance_eur": 5000.0,
            "overdraft_limit_eur": 0.0,
        },
        "DE89929842579913662103": {
            "account_id": "ACC-2002",
            "iban": "DE89929842579913662103",
            "customer_name": "카리나",
            "current_balance_eur": 2100.0,
            "overdraft_limit_eur": 0.0,
        },
        "DE44500105175407324931": {
            "account_id": "ACC-2003",
            "iban": "DE44500105175407324931",
            "customer_name": "안유진",
            "current_balance_eur": 8200.0,
            "overdraft_limit_eur": 500.0,
        },
        "DE12500105170648489890": {
            "account_id": "ACC-2004",
            "iban": "DE12500105170648489890",
            "customer_name": "민지",
            "current_balance_eur": 13450.0,
            "overdraft_limit_eur": 1000.0,
        },
        "DE75512108001245126199": {
            "account_id": "ACC-2005",
            "iban": "DE75512108001245126199",
            "customer_name": "해린",
            "current_balance_eur": 930.0,
            "overdraft_limit_eur": 300.0,
        },
        "DE02120300000000202051": {
            "account_id": "ACC-2006",
            "iban": "DE02120300000000202051",
            "customer_name": "지민",
            "current_balance_eur": 26780.0,
            "overdraft_limit_eur": 2000.0,
        },
        "DE91100000000123456789": {
            "account_id": "ACC-2007",
            "iban": "DE91100000000123456789",
            "customer_name": "정국",
            "current_balance_eur": 1450.0,
            "overdraft_limit_eur": 150.0,
        },
        "DE66100205000009876543": {
            "account_id": "ACC-2008",
            "iban": "DE66100205000009876543",
            "customer_name": "차은우",
            "current_balance_eur": 7120.0,
            "overdraft_limit_eur": 800.0,
        },
        "DE44500105170011112222": {
            "account_id": "ACC-2009",
            "iban": "DE44500105170011112222",
            "customer_name": "김하늘",
            "current_balance_eur": 3150.0,
            "overdraft_limit_eur": 0.0,
        },
        "DE77500105170033334444": {
            "account_id": "ACC-2010",
            "iban": "DE77500105170033334444",
            "customer_name": "박서준",
            "current_balance_eur": 11890.0,
            "overdraft_limit_eur": 1200.0,
        },
    },
    "transactions": [
        {
            "transaction_id": "TX-10001",
            "account_id": "ACC-2001",
            "booking_ts": "2026-04-10T09:00:00+00:00",
            "amount_eur": 2600.0,
            "type": "deposit",
            "description": "Salary deposit",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10002",
            "account_id": "ACC-2001",
            "booking_ts": "2026-04-11T14:20:00+00:00",
            "amount_eur": -120.0,
            "type": "purchase",
            "description": "Online shopping",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10003",
            "account_id": "ACC-2001",
            "booking_ts": "2026-04-13T08:10:00+00:00",
            "amount_eur": -45.0,
            "type": "withdrawal",
            "description": "ATM withdrawal",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10004",
            "account_id": "ACC-2001",
            "booking_ts": "2026-04-14T11:30:00+00:00",
            "amount_eur": 2565.0,
            "type": "deposit",
            "description": "Project incentive",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10005",
            "account_id": "ACC-2002",
            "booking_ts": "2026-04-08T10:00:00+00:00",
            "amount_eur": 1800.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10006",
            "account_id": "ACC-2002",
            "booking_ts": "2026-04-10T13:45:00+00:00",
            "amount_eur": -55.0,
            "type": "purchase",
            "description": "Coffee machine",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10007",
            "account_id": "ACC-2002",
            "booking_ts": "2026-04-12T17:25:00+00:00",
            "amount_eur": 355.0,
            "type": "deposit",
            "description": "Expense reimbursement",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10008",
            "account_id": "ACC-2003",
            "booking_ts": "2026-04-09T16:00:00+00:00",
            "amount_eur": 8200.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10009",
            "account_id": "ACC-2003",
            "booking_ts": "2026-04-11T09:50:00+00:00",
            "amount_eur": -180.0,
            "type": "purchase",
            "description": "Airline ticket",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10010",
            "account_id": "ACC-2003",
            "booking_ts": "2026-04-13T15:30:00+00:00",
            "amount_eur": 180.0,
            "type": "refund",
            "description": "Ticket refund",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10011",
            "account_id": "ACC-2004",
            "booking_ts": "2026-04-07T08:30:00+00:00",
            "amount_eur": 12000.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10012",
            "account_id": "ACC-2004",
            "booking_ts": "2026-04-10T12:00:00+00:00",
            "amount_eur": 1450.0,
            "type": "deposit",
            "description": "Consulting payout",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10013",
            "account_id": "ACC-2005",
            "booking_ts": "2026-04-06T11:15:00+00:00",
            "amount_eur": 1000.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10014",
            "account_id": "ACC-2005",
            "booking_ts": "2026-04-08T19:10:00+00:00",
            "amount_eur": -70.0,
            "type": "purchase",
            "description": "Book store",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10015",
            "account_id": "ACC-2006",
            "booking_ts": "2026-04-05T07:45:00+00:00",
            "amount_eur": 25000.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10016",
            "account_id": "ACC-2006",
            "booking_ts": "2026-04-09T13:00:00+00:00",
            "amount_eur": 1780.0,
            "type": "deposit",
            "description": "Bonus payout",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10017",
            "account_id": "ACC-2007",
            "booking_ts": "2026-04-10T20:30:00+00:00",
            "amount_eur": 1500.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10018",
            "account_id": "ACC-2007",
            "booking_ts": "2026-04-12T18:00:00+00:00",
            "amount_eur": -50.0,
            "type": "purchase",
            "description": "Streaming subscription",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10019",
            "account_id": "ACC-2008",
            "booking_ts": "2026-04-04T09:40:00+00:00",
            "amount_eur": 7000.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10020",
            "account_id": "ACC-2008",
            "booking_ts": "2026-04-13T10:05:00+00:00",
            "amount_eur": 120.0,
            "type": "deposit",
            "description": "Cashback",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10021",
            "account_id": "ACC-2009",
            "booking_ts": "2026-04-08T08:00:00+00:00",
            "amount_eur": 3000.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10022",
            "account_id": "ACC-2009",
            "booking_ts": "2026-04-12T12:10:00+00:00",
            "amount_eur": 150.0,
            "type": "deposit",
            "description": "Travel reimbursement",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10023",
            "account_id": "ACC-2010",
            "booking_ts": "2026-04-06T10:20:00+00:00",
            "amount_eur": 11900.0,
            "type": "deposit",
            "description": "Initial balance",
            "counterparty_iban": None,
        },
        {
            "transaction_id": "TX-10024",
            "account_id": "ACC-2010",
            "booking_ts": "2026-04-11T09:15:00+00:00",
            "amount_eur": -10.0,
            "type": "fee",
            "description": "International transfer fee",
            "counterparty_iban": None,
        },
    ],
    "credentials": {
        "teller_username": "teller",
        "teller_password": "teller123",
    },
}


# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------
def q2(value: Decimal | float | int | str) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@serialized_write
def ensure_seed_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    hr_seed, bank_seed = deepcopy(DEFAULT_HR_USERS), deepcopy(DEFAULT_BANK_DATA)
    add_classroom_records(hr_seed, bank_seed, TRAINING_STUDENTS)
    if not HR_JSON_PATH.exists():
        save_json(HR_JSON_PATH, hr_seed)
    if not BANK_JSON_PATH.exists():
        save_json(BANK_JSON_PATH, bank_seed)


def load_json(path: Path) -> Any:
    with DATA_LOCK:
        if not path.exists():
            raise HTTPException(status_code=500, detail=f"Data file missing: {path.name}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)


def save_json(path: Path, data: Any) -> None:
    with DATA_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False,
            ) as f:
                temporary = Path(f.name)
                json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def authenticate_teller(username: Optional[str], password: Optional[str], bank_data: dict[str, Any]) -> None:
    creds = bank_data.get("credentials", {})
    expected_username = creds.get("teller_username", TELLER_USERNAME)
    expected_password = creds.get("teller_password", TELLER_PASSWORD)
    if (username or expected_username) != expected_username or (password or expected_password) != expected_password:
        raise HTTPException(status_code=401, detail="Bad credentials")


def get_hr_user(hr_data: dict[str, Any], name: str) -> dict[str, Any]:
    user = hr_data.get(name)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_bank_account(bank_data: dict[str, Any], iban: str) -> dict[str, Any]:
    account = bank_data.get("accounts", {}).get(iban)
    if not account:
        raise HTTPException(status_code=404, detail="IBAN not found")
    return account


def get_recent_transactions(bank_data: dict[str, Any], account_id: str, limit: int = 10) -> list[dict[str, Any]]:
    txs = [tx for tx in bank_data.get("transactions", []) if tx["account_id"] == account_id]
    txs.sort(key=lambda x: x["booking_ts"], reverse=True)
    return txs[:limit]


def calculate_time_off_days(from_date: date, to_date: date) -> int:
    if to_date < from_date:
        raise HTTPException(status_code=400, detail="to_date must be on or after from_date")
    return (to_date - from_date).days + 1


def next_employee_id(hr_data: dict[str, Any]) -> str:
    max_num = 1000
    for user in hr_data.values():
        raw = str(user.get("user_id", "EMP-1000"))
        try:
            max_num = max(max_num, int(raw.split("-")[-1]))
        except ValueError:
            continue
    return f"EMP-{max_num + 1}"


def new_transaction(account_id: str, amount_eur: float, tx_type: str, description: str, counterparty_iban: Optional[str] = None) -> dict[str, Any]:
    return {
        "transaction_id": f"TX-{uuid.uuid4().hex[:10].upper()}",
        "account_id": account_id,
        "booking_ts": now_iso(),
        "amount_eur": q2(amount_eur),
        "type": tx_type,
        "description": description,
        "counterparty_iban": counterparty_iban,
    }


# -------------------------------------------------------------------
# Banking schemas
# -------------------------------------------------------------------
class IbanTransferRequest(BaseModel):
    source_iban: str = Field(..., examples=["DE89320895326389021994"])
    destination_iban: str = Field(..., examples=["DE89929842579913662103"])
    amount_eur: float = Field(..., gt=0, examples=[100.5])
    username: Optional[str] = Field(default=TELLER_USERNAME)
    password: Optional[str] = Field(default=TELLER_PASSWORD)


class IbanTransferResponse(BaseModel):
    status: str
    source_iban: str
    destination_iban: str
    amount_eur: float
    debit_tx: str
    credit_tx: str
    timestamp: str
    new_balance_eur: float


class BalanceInquiryRequest(BaseModel):
    iban: str = Field(..., examples=["DE89320895326389021994"])
    username: Optional[str] = Field(default=TELLER_USERNAME)
    password: Optional[str] = Field(default=TELLER_PASSWORD)


class RecentTransaction(BaseModel):
    transaction_id: str
    account_id: str
    booking_ts: str
    amount_eur: float
    type: str
    description: Optional[str] = None
    counterparty_iban: Optional[str] = None


class BalanceInquiryResponse(BaseModel):
    iban: str
    account_id: str
    current_balance_eur: float
    overdraft_limit_eur: float
    available_balance_eur: float
    recent_transactions: list[RecentTransaction]


class FeeReversalRequest(BaseModel):
    iban: str = Field(..., examples=["DE89320895326389021994"])
    amount_eur: float = Field(..., gt=0, examples=[50])


class FeeReversalResponse(BaseModel):
    status: str
    iban: str
    customer_name: str
    amount_eur: float
    transaction_id: str
    booking_ts: str
    new_balance_eur: float
    message: str


class ApproveOverdraftRequest(BaseModel):
    iban: str = Field(..., examples=["DE89320895326389021994"])
    overdraft_limit_eur: float = Field(..., ge=0, le=10000, examples=[5000])

    @field_validator("overdraft_limit_eur")
    @classmethod
    def validate_limit(cls, value: float) -> float:
        if value < 0 or value > 10000:
            raise ValueError("Overdraft limit must be between 0 and 10,000 EUR")
        return value


class ApproveOverdraftResponse(BaseModel):
    account_id: str
    iban: str
    customer_name: str
    overdraft_limit_eur: float
    message: str


# -------------------------------------------------------------------
# HR schemas
# -------------------------------------------------------------------
class UserProfileResponse(BaseModel):
    name: str
    title: str
    address: str
    time_off_balance: int


class TimeOffRequest(BaseModel):
    name: str = Field(..., description="The name of the user.")
    from_date: date = Field(..., description="Start date of the time-off request (YYYY-MM-DD).")
    to_date: date = Field(..., description="End date of the time-off request (YYYY-MM-DD).")


class UpdateTitleRequest(BaseModel):
    name: str
    new_title: str


class UpdateAddressRequest(BaseModel):
    name: str
    new_address: str


class CreateUserRequest(BaseModel):
    name: str
    time_off_balance: int = Field(..., ge=0)
    title: str
    address: str


# -------------------------------------------------------------------
# Startup
# -------------------------------------------------------------------
@app.on_event("startup")
def startup_event() -> None:
    ensure_seed_files()


# -------------------------------------------------------------------
# Common
# -------------------------------------------------------------------
@app.get("/health", tags=["common"])
def health() -> dict[str, str]:
    return {"status": "ok"}


# -------------------------------------------------------------------
# Banking endpoints
# -------------------------------------------------------------------
@app.post("/iban-transfer", response_model=IbanTransferResponse, tags=["banking"])
@serialized_write
def iban_transfer(payload: IbanTransferRequest) -> IbanTransferResponse:
    bank_data = load_json(BANK_JSON_PATH)
    authenticate_teller(payload.username, payload.password, bank_data)

    if payload.source_iban == payload.destination_iban:
        raise HTTPException(status_code=400, detail="Source and destination IBAN must be different")

    source = get_bank_account(bank_data, payload.source_iban)
    destination = get_bank_account(bank_data, payload.destination_iban)

    amount = q2(payload.amount_eur)
    available = q2(source["current_balance_eur"] + source.get("overdraft_limit_eur", 0))
    if available < amount:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Insufficient funds. Balance {q2(source['current_balance_eur'])}, "
                f"overdraft {q2(source.get('overdraft_limit_eur', 0))}"
            ),
        )

    source["current_balance_eur"] = q2(source["current_balance_eur"] - amount)
    destination["current_balance_eur"] = q2(destination["current_balance_eur"] + amount)

    debit = new_transaction(
        source["account_id"],
        -amount,
        "transfer_out",
        f"Transfer to {payload.destination_iban}",
        payload.destination_iban,
    )
    credit = new_transaction(
        destination["account_id"],
        amount,
        "transfer_in",
        f"Transfer from {payload.source_iban}",
        payload.source_iban,
    )

    bank_data["transactions"].append(debit)
    bank_data["transactions"].append(credit)
    save_json(BANK_JSON_PATH, bank_data)

    return IbanTransferResponse(
        status="success",
        source_iban=payload.source_iban,
        destination_iban=payload.destination_iban,
        amount_eur=amount,
        debit_tx=debit["transaction_id"],
        credit_tx=credit["transaction_id"],
        timestamp=debit["booking_ts"],
        new_balance_eur=q2(source["current_balance_eur"]),
    )


@app.post("/balance-inquiry", response_model=BalanceInquiryResponse, tags=["banking"])
def balance_inquiry(payload: BalanceInquiryRequest) -> BalanceInquiryResponse:
    bank_data = load_json(BANK_JSON_PATH)
    authenticate_teller(payload.username, payload.password, bank_data)
    account = get_bank_account(bank_data, payload.iban)
    recent_transactions = get_recent_transactions(bank_data, account["account_id"])
    current_balance = q2(account["current_balance_eur"])
    overdraft_limit = q2(account.get("overdraft_limit_eur", 0))
    available_balance = q2(current_balance + overdraft_limit)

    return BalanceInquiryResponse(
        iban=account["iban"],
        account_id=account["account_id"],
        current_balance_eur=current_balance,
        overdraft_limit_eur=overdraft_limit,
        available_balance_eur=available_balance,
        recent_transactions=[RecentTransaction(**tx) for tx in recent_transactions],
    )


@app.post("/fee-reversal", response_model=FeeReversalResponse, tags=["banking"])
@serialized_write
def fee_reversal(payload: FeeReversalRequest) -> FeeReversalResponse:
    bank_data = load_json(BANK_JSON_PATH)
    account = get_bank_account(bank_data, payload.iban)
    amount = q2(payload.amount_eur)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    account["current_balance_eur"] = q2(account["current_balance_eur"] + amount)
    tx = new_transaction(
        account["account_id"],
        amount,
        "fee_reversal",
        "Fee reversal posted",
        None,
    )
    bank_data["transactions"].append(tx)
    save_json(BANK_JSON_PATH, bank_data)

    return FeeReversalResponse(
        status="success",
        iban=account["iban"],
        customer_name=account["customer_name"],
        amount_eur=amount,
        transaction_id=tx["transaction_id"],
        booking_ts=tx["booking_ts"],
        new_balance_eur=q2(account["current_balance_eur"]),
        message=f"Fee reversal of {amount:.2f} EUR processed successfully.",
    )


@app.post("/approve-overdraft", response_model=ApproveOverdraftResponse, tags=["banking"])
@serialized_write
def approve_overdraft(payload: ApproveOverdraftRequest) -> ApproveOverdraftResponse:
    bank_data = load_json(BANK_JSON_PATH)
    account = get_bank_account(bank_data, payload.iban)
    limit = q2(payload.overdraft_limit_eur)
    if limit < 0 or limit > 10000:
        raise HTTPException(status_code=400, detail="Overdraft limit must be between 0 and 10,000 EUR")

    account["overdraft_limit_eur"] = limit
    save_json(BANK_JSON_PATH, bank_data)

    return ApproveOverdraftResponse(
        account_id=account["account_id"],
        iban=account["iban"],
        customer_name=account["customer_name"],
        overdraft_limit_eur=limit,
        message=f"Overdraft limit updated to {limit:.2f} EUR.",
    )


# -------------------------------------------------------------------
# HR endpoints
# -------------------------------------------------------------------
@app.get("/user_profile_details/{name}", response_model=UserProfileResponse, tags=["hr"])
def get_user_profile(name: str) -> UserProfileResponse:
    hr_data = load_json(HR_JSON_PATH)
    user = get_hr_user(hr_data, name)
    return UserProfileResponse(
        name=user["name"],
        title=user["title"],
        address=user["address"],
        time_off_balance=int(user["time_off_balance"]),
    )


@app.get("/time-off-balance/{name}", response_model=str, tags=["hr"])
def get_time_off_balance(name: str) -> str:
    hr_data = load_json(HR_JSON_PATH)
    user = get_hr_user(hr_data, name)
    return str(user["time_off_balance"])


@app.post("/request-time-off", response_model=str, tags=["hr"])
@serialized_write
def request_time_off(payload: TimeOffRequest) -> str:
    hr_data = load_json(HR_JSON_PATH)
    user = get_hr_user(hr_data, payload.name)
    requested_days = calculate_time_off_days(payload.from_date, payload.to_date)
    remaining_days = int(user["time_off_balance"])

    if requested_days > remaining_days:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient time off balance. Remaining balance: {remaining_days} days",
        )

    user["time_off_balance"] = remaining_days - requested_days
    save_json(HR_JSON_PATH, hr_data)

    return (
        f"Time off request approved for {payload.name} from {payload.from_date.isoformat()} "
        f"to {payload.to_date.isoformat()} ({requested_days} days). "
        f"Remaining balance: {user['time_off_balance']} days."
    )


@app.put("/update-title", response_model=str, tags=["hr"])
@serialized_write
def update_title(payload: UpdateTitleRequest) -> str:
    hr_data = load_json(HR_JSON_PATH)
    user = get_hr_user(hr_data, payload.name)
    old_title = user["title"]
    user["title"] = payload.new_title
    save_json(HR_JSON_PATH, hr_data)
    return f"Title for {payload.name} updated from '{old_title}' to '{payload.new_title}'."


@app.put("/update-address", response_model=str, tags=["hr"])
@serialized_write
def update_address(payload: UpdateAddressRequest) -> str:
    hr_data = load_json(HR_JSON_PATH)
    user = get_hr_user(hr_data, payload.name)
    old_address = user["address"]
    user["address"] = payload.new_address
    save_json(HR_JSON_PATH, hr_data)
    return f"Address for {payload.name} updated from '{old_address}' to '{payload.new_address}'."


@app.post("/create-user", response_model=str, tags=["hr"])
@serialized_write
def create_user(payload: CreateUserRequest) -> str:
    hr_data = load_json(HR_JSON_PATH)
    if payload.name in hr_data:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = next_employee_id(hr_data)
    hr_data[payload.name] = {
        "user_id": user_id,
        "name": payload.name,
        "title": payload.title,
        "address": payload.address,
        "time_off_balance": int(payload.time_off_balance),
    }
    save_json(HR_JSON_PATH, hr_data)
    return f"User created successfully. user_id={user_id}"
