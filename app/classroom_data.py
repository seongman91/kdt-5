"""Deterministic fictional records for a shared training server."""
from __future__ import annotations

from typing import Any


def training_iban(student: int, destination: bool = False) -> str:
    # Deliberately fictional bank code. Check digits are valid for lab validators.
    bban = "99999999" + f"{student * 2 + int(destination):010d}"
    checksum = 98 - int(bban + "131400") % 97
    return f"DE{checksum:02d}{bban}"


def classroom_roster(count: int) -> list[dict[str, str]]:
    if not 0 <= count <= 999:
        raise ValueError("TRAINING_STUDENTS must be between 0 and 999")
    return [
        {
            "student": f"S{index:02d}",
            "hr_name": f"교육생{index:02d}",
            "source_iban": training_iban(index),
            "destination_iban": training_iban(index, True),
        }
        for index in range(1, count + 1)
    ]


def add_classroom_records(
    hr_data: dict[str, Any], bank_data: dict[str, Any], count: int
) -> None:
    for row in classroom_roster(count):
        student, name = row["student"], row["hr_name"]
        hr_data.setdefault(name, {
            "user_id": f"CLASS-{student}", "name": name,
            "title": "Training Analyst", "address": f"교육용 초기 주소 {student}",
            "time_off_balance": 15,
        })
        for role, balance in (("source", 5000.0), ("destination", 1000.0)):
            iban = row[f"{role}_iban"]
            bank_data.setdefault("accounts", {}).setdefault(iban, {
                "account_id": f"CLASS-{student}-{role.upper()}",
                "iban": iban, "customer_name": f"{name}-{role}",
                "current_balance_eur": balance, "overdraft_limit_eur": 0.0,
            })
    bank_data.setdefault("transactions", [])
