import logging
from copy import deepcopy
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from src.db.models import Customer
from tests.helpers import generate_create_customer_data
from tests.helpers import generate_field
from tests.helpers import generate_random_db_customer
from tests.helpers import validate_customer_response
from tests.helpers import validate_db_customer

logger = logging.getLogger(__name__)


def test_get_customers_as_admin(api_client: TestClient, mock_db: MagicMock) -> None:
    mock_admin = generate_random_db_customer(is_admin=True)
    mock_user = generate_random_db_customer()
    mock_db.scalars.return_value.all.return_value = [mock_admin, mock_user]

    response = api_client.get(
        "/customers",
        headers={"x-customer-id": str(mock_admin.id), "x-is-admin": "true"},
    )

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)

    assert len(response_json) == 2
    validate_customer_response(response_json[0], mock_admin)
    validate_customer_response(response_json[1], mock_user)


def test_get_customers_as_non_admin(api_client: TestClient, mock_db: MagicMock) -> None:
    mock_user = generate_random_db_customer()

    def _get_customer(_: Any, customer_id: str) -> Customer:
        assert customer_id == str(mock_user.id)
        return mock_user

    mock_db.get = _get_customer

    response = api_client.get(
        "/customers",
        headers={"x-customer-id": str(mock_user.id), "x-is-admin": "false"},
    )

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)

    assert len(response_json) == 1
    validate_customer_response(response_json[0], mock_user)


@pytest.mark.parametrize("customer_id", ("str", "123", str(uuid4()) + "a"))
@pytest.mark.parametrize("is_admin", (True, False))
def test_get_customer_wrong_id(
    api_client: TestClient, customer_id: str, is_admin: bool
) -> None:
    response = api_client.get(
        f"/customers/{customer_id}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": str(is_admin).lower()},
    )
    assert response.status_code == 422


def test_get_customer_not_found(api_client: TestClient, mock_db: MagicMock) -> None:
    customer_id = str(uuid4())

    def _get_customer(_: Any, user_id: UUID) -> None:
        assert str(user_id) == customer_id
        return None

    mock_db.get = _get_customer

    response = api_client.get(
        f"/customers/{customer_id}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "true"},
    )
    assert response.status_code == 404


def test_get_customer_different_id_as_non_admin(api_client: TestClient) -> None:
    response = api_client.get(
        f"/customers/{str(uuid4())}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "false"},
    )
    assert response.status_code == 403


def test_get_customer_different_id_as_admin(
    api_client: TestClient, mock_db: MagicMock
) -> None:
    mock_user = generate_random_db_customer()

    def _get_customer(_: Any, customer_id: str) -> Customer:
        assert customer_id == mock_user.id
        return mock_user

    mock_db.get = _get_customer

    response = api_client.get(
        f"/customers/{str(mock_user.id)}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "true"},
    )

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)

    validate_customer_response(response_json, mock_user)


@pytest.mark.parametrize("is_admin", (True, False))
def test_get_customer_correct(
    api_client: TestClient, mock_db: MagicMock, is_admin: bool
) -> None:
    mock_user = generate_random_db_customer()

    def _get_customer(_: Any, customer_id: str) -> Customer:
        assert customer_id == mock_user.id
        return mock_user

    mock_db.get = _get_customer

    response = api_client.get(
        f"/customers/{str(mock_user.id)}",
        headers={
            "x-customer-id": str(mock_user.id),
            "x-is-admin": str(is_admin).lower(),
        },
    )

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)

    validate_customer_response(response_json, mock_user)


def test_create_customer_correct(api_client: TestClient, mock_db: MagicMock) -> None:
    customer_data = generate_create_customer_data()
    expected_customers = []

    def _add_customer(customer: Customer) -> None:
        assert customer.username == customer_data["username"]
        validate_db_customer(customer, customer_data)

    def _db_refresh(customer: Customer) -> None:
        customer.id = uuid4()  # type: ignore[assignment]
        customer.created_at = datetime.now()  # type: ignore[assignment]
        customer.is_admin = False  # type: ignore[assignment]
        expected_customers.append(customer)

    mock_db.add = _add_customer
    mock_db.refresh = _db_refresh

    response = api_client.post("/customers/create", json=customer_data)

    assert response.status_code == 201
    response_json = response.json()
    assert isinstance(response_json, dict)

    validate_customer_response(response_json, expected_customers[0])


@pytest.mark.parametrize(
    "field",
    ("username", "password", "first_name", "last_name", "email", "address", "phone"),
)
def test_create_customer_missing_field(api_client: TestClient, field: str) -> None:
    customer_data = generate_create_customer_data()
    customer_data.pop(field)

    response = api_client.post("/customers/create", json=customer_data)
    assert response.status_code == 422


def test_create_customer_additional_field(api_client: TestClient) -> None:
    customer_data = generate_create_customer_data()
    customer_data["additional"] = "abcd"

    response = api_client.post("/customers/create", json=customer_data)
    assert response.status_code == 422


def test_create_customer_db_error(api_client: TestClient, mock_db: MagicMock) -> None:
    customer_data = generate_create_customer_data()

    mock_db.commit.side_effect = IntegrityError(
        statement="DB error", params=None, orig=BaseException("DB error\nVery serious")
    )

    response = api_client.post("/customers/create", json=customer_data)
    assert response.status_code == 400
    mock_db.rollback.assert_called_once()


@pytest.mark.parametrize("customer_id", ("str", "123", str(uuid4()) + "a"))
@pytest.mark.parametrize("is_admin", (True, False))
def test_update_customer_wrong_id(
    api_client: TestClient, customer_id: str, is_admin: bool
) -> None:
    update_data = generate_create_customer_data()
    update_data.pop("username")

    response = api_client.patch(
        f"/customers/{customer_id}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": str(is_admin).lower()},
        json=update_data,
    )
    assert response.status_code == 422


def test_update_customer_not_found(api_client: TestClient, mock_db: MagicMock) -> None:
    customer_id = str(uuid4())

    def _get_customer(_: Any, user_id: UUID) -> None:
        assert str(user_id) == customer_id
        return None

    mock_db.get = _get_customer

    update_data = generate_create_customer_data()
    update_data.pop("username")

    response = api_client.patch(
        f"/customers/{customer_id}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "true"},
        json=update_data,
    )
    assert response.status_code == 404


def test_update_customer_different_id_as_non_admin(api_client: TestClient) -> None:
    update_data = generate_create_customer_data()
    update_data.pop("username")

    response = api_client.patch(
        f"/customers/{str(uuid4())}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "false"},
        json=update_data,
    )
    assert response.status_code == 403


def test_update_customer_different_id_as_admin(
    api_client: TestClient, mock_db: MagicMock
) -> None:
    mock_user = generate_random_db_customer()
    orig_username = mock_user.username
    orig_id = mock_user.id
    orig_created_at = mock_user.created_at

    def _get_customer(_: Any, customer_id: str) -> Customer:
        assert customer_id == mock_user.id
        return mock_user

    mock_db.get = _get_customer

    update_data = generate_create_customer_data()
    update_data.pop("username")

    response = api_client.patch(
        f"/customers/{str(mock_user.id)}",
        headers={
            "x-customer-id": str(uuid4()),
            "x-is-admin": "true",
        },
        json=update_data,
    )

    mock_db.commit.assert_called_once()
    assert mock_user.id == orig_id
    assert mock_user.username == orig_username
    assert mock_user.created_at == orig_created_at
    assert mock_user.is_admin is False
    validate_db_customer(mock_user, update_data)

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)

    validate_customer_response(response_json, mock_user)


@pytest.mark.parametrize("is_admin", (True, False))
def test_update_customer_all_fields(
    api_client: TestClient, mock_db: MagicMock, is_admin: bool
) -> None:
    mock_user = generate_random_db_customer()
    orig_username = mock_user.username
    orig_id = mock_user.id
    orig_created_at = mock_user.created_at

    def _get_customer(_: Any, customer_id: str) -> Customer:
        assert customer_id == mock_user.id
        return mock_user

    mock_db.get = _get_customer

    update_data = generate_create_customer_data()
    update_data.pop("username")

    response = api_client.patch(
        f"/customers/{str(mock_user.id)}",
        headers={
            "x-customer-id": str(mock_user.id),
            "x-is-admin": str(is_admin).lower(),
        },
        json=update_data,
    )

    mock_db.commit.assert_called_once()
    assert mock_user.id == orig_id
    assert mock_user.username == orig_username
    assert mock_user.created_at == orig_created_at
    assert mock_user.is_admin is False
    validate_db_customer(mock_user, update_data)

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)

    validate_customer_response(response_json, mock_user)


@pytest.mark.parametrize(
    "field", ("password", "first_name", "last_name", "email", "address", "phone")
)
@pytest.mark.parametrize("is_admin", (True, False))
def test_update_customer_single_field(
    api_client: TestClient, mock_db: MagicMock, is_admin: bool, field: str
) -> None:
    mock_user = generate_random_db_customer()
    orig_user = deepcopy(mock_user)

    def _get_customer(_: Any, customer_id: str) -> Customer:
        assert customer_id == mock_user.id
        return mock_user

    mock_db.get = _get_customer

    update_data = {field: generate_field(field)}

    response = api_client.patch(
        f"/customers/{str(mock_user.id)}",
        headers={
            "x-customer-id": str(mock_user.id),
            "x-is-admin": str(is_admin).lower(),
        },
        json=update_data,
    )

    mock_db.commit.assert_called_once()
    if field == "password":
        assert bcrypt.checkpw(
            update_data["password"].encode("utf-8"), mock_user.password.encode("utf-8")
        )
    else:
        assert getattr(mock_user, field) == update_data[field]

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)

    setattr(orig_user, field, getattr(mock_user, field))
    validate_customer_response(response_json, orig_user)


@pytest.mark.parametrize("is_admin", (True, False))
def test_update_customer_username(api_client: TestClient, is_admin: bool) -> None:
    update_data = generate_create_customer_data()

    response = api_client.patch(
        f"/customers/{str(uuid4())}",
        headers={
            "x-customer-id": str(uuid4()),
            "x-is-admin": str(is_admin).lower(),
        },
        json=update_data,
    )
    assert response.status_code == 422


def test_update_customer_db_error(api_client: TestClient, mock_db: MagicMock) -> None:
    mock_user = generate_random_db_customer()

    def _get_customer(_: Any, customer_id: str) -> Customer:
        assert customer_id == mock_user.id
        return mock_user

    mock_db.get = _get_customer

    update_data = generate_create_customer_data()
    update_data.pop("username")

    mock_db.commit.side_effect = IntegrityError(
        statement="DB error", params=None, orig=BaseException("DB error\nVery serious")
    )

    response = api_client.patch(
        f"/customers/{str(mock_user.id)}",
        headers={
            "x-customer-id": str(mock_user.id),
            "x-is-admin": "true",
        },
        json=update_data,
    )
    assert response.status_code == 400
    mock_db.rollback.assert_called_once()
