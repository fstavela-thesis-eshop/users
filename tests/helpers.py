from collections.abc import Callable
from datetime import datetime
from functools import partial
from random import choice
from random import choices
from string import ascii_letters
from string import digits
from string import punctuation
from typing import Any
from uuid import uuid4

import bcrypt

from src.db.models import Customer

EXPECTED_CUSTOMER_RESPONSE_FIELDS = {
    "id",
    "username",
    "first_name",
    "last_name",
    "email",
    "address",
    "phone",
    "created_at",
}


def gen_str(
    length: int = 10,
    *,
    use_letters: bool = True,
    use_digits: bool = True,
    use_punctuation: bool = True,
) -> str:
    symbols = ""
    if use_letters:
        symbols += ascii_letters
    if use_digits:
        symbols += digits
    if use_punctuation:
        symbols += punctuation
    return "".join(choices(symbols, k=length))


def gen_email() -> str:
    return (
        f"{gen_str(use_punctuation=False)}@"
        f"{gen_str(use_digits=False, use_punctuation=False).lower()}."
        f"{choice(('com', 'org', 'net', 'edu', 'gov', 'cz', 'sk'))}"
    )


def gen_phone() -> str:
    return f"+420 {gen_str(9, use_letters=False, use_punctuation=False)}"


FIELD_GENERATORS: dict[str, Callable[..., str]] = {
    "username": partial(gen_str, use_punctuation=False),
    "password": gen_str,
    "first_name": partial(gen_str, use_digits=False, use_punctuation=False),
    "last_name": partial(gen_str, use_digits=False, use_punctuation=False),
    "email": gen_email,
    "address": partial(gen_str, 50),
    "phone": gen_phone,
}


def generate_random_db_customer(*, is_admin: bool = False) -> Customer:
    hashed_password = bcrypt.hashpw(gen_str().encode("utf-8"), bcrypt.gensalt())
    return Customer(
        id=uuid4(),
        username=FIELD_GENERATORS["username"](),
        password=hashed_password.decode("utf-8"),
        first_name=FIELD_GENERATORS["first_name"](),
        last_name=FIELD_GENERATORS["last_name"](),
        email=FIELD_GENERATORS["email"](),
        address=FIELD_GENERATORS["address"](),
        phone=FIELD_GENERATORS["phone"](),
        created_at=datetime.now(),
        is_admin=is_admin,
    )


def generate_create_customer_data() -> dict[str, str]:
    return {
        "username": FIELD_GENERATORS["username"](),
        "password": FIELD_GENERATORS["password"](),
        "first_name": FIELD_GENERATORS["first_name"](),
        "last_name": FIELD_GENERATORS["last_name"](),
        "email": FIELD_GENERATORS["email"](),
        "address": FIELD_GENERATORS["address"](),
        "phone": FIELD_GENERATORS["phone"](),
    }


def generate_field(field: str) -> str:
    return FIELD_GENERATORS[field]()


def validate_customer_response(
    response_customer: dict[str, Any], expected_customer: Customer
) -> None:
    assert len(response_customer.keys()) == len(EXPECTED_CUSTOMER_RESPONSE_FIELDS)
    assert set(response_customer.keys()) == EXPECTED_CUSTOMER_RESPONSE_FIELDS
    for field in EXPECTED_CUSTOMER_RESPONSE_FIELDS:
        expected_value = getattr(expected_customer, field)
        if isinstance(expected_value, datetime):
            expected_value = expected_value.isoformat()
        else:
            expected_value = str(expected_value)
        assert response_customer[field] == expected_value, (
            f"{response_customer[field]} != {expected_value}"
        )


def validate_db_customer(db_customer: Customer, expected_data: dict[str, Any]) -> None:
    assert bcrypt.checkpw(
        expected_data["password"].encode("utf-8"), db_customer.password.encode("utf-8")
    )
    assert db_customer.first_name == expected_data["first_name"]
    assert db_customer.last_name == expected_data["last_name"]
    assert db_customer.email == expected_data["email"]
    assert db_customer.address == expected_data["address"]
    assert db_customer.phone == expected_data["phone"]
