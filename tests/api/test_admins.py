import logging
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pytest_mock.plugin import MockerFixture
from sqlalchemy import Select
from sqlalchemy import select

from db.models import Customer
from tests.helpers import generate_random_db_customer

logger = logging.getLogger(__name__)


def test_get_admins_forbidden(api_client: TestClient) -> None:
    response = api_client.get(
        "/admins", headers={"x-customer-id": str(uuid4()), "x-is-admin": "false"}
    )
    assert response.status_code == 403


def test_get_admins_success(
    api_client: TestClient, mock_db: MagicMock, mocker: MockerFixture
) -> None:
    mock_admin1 = generate_random_db_customer(is_admin=True)
    mock_admin2 = generate_random_db_customer(is_admin=True)

    mock_return = mocker.Mock()

    def _scalars(query: Select[Customer.id]) -> mocker.Mock:
        assert str(query.compile()) == str(
            select(Customer.id).where(Customer.is_admin).compile()
        )
        return mock_return

    mock_db.scalars = _scalars
    mock_return.all.return_value = [mock_admin1.id, mock_admin2.id]

    response = api_client.get(
        "/admins",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "true"},
    )

    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)

    assert len(response_json) == 2
    assert response_json == [str(mock_admin1.id), str(mock_admin2.id)]


def test_add_admin_forbidden(api_client: TestClient) -> None:
    response = api_client.put(
        f"/admins/{str(uuid4())}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "false"},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("customer_id", ("str", "123", str(uuid4()) + "a"))
def test_add_admin_wrong_id(
    api_client: TestClient,
    customer_id: str,
) -> None:
    response = api_client.put(
        f"/admins/{customer_id}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "true"},
    )
    assert response.status_code == 422


def test_add_admin_not_found(api_client: TestClient, mock_db: MagicMock) -> None:
    customer_id = str(uuid4())

    def _get_customer(_: Any, user_id: UUID) -> None:
        assert str(user_id) == customer_id
        return None

    mock_db.get = _get_customer

    response = api_client.put(
        f"/admins/{customer_id}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "true"},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("was_admin", (True, False))
def test_add_admin_success(
    api_client: TestClient, mock_db: MagicMock, was_admin: bool
) -> None:
    mock_admin = generate_random_db_customer(is_admin=True)
    mock_user = generate_random_db_customer(is_admin=was_admin)

    def _get_customer(_: Any, user_id: UUID) -> Customer:
        assert user_id == mock_user.id
        return mock_user

    mock_db.get = _get_customer

    response = api_client.put(
        f"/admins/{str(mock_user.id)}",
        headers={"x-customer-id": str(mock_admin.id), "x-is-admin": "true"},
    )
    assert response.status_code == 204

    assert mock_user.is_admin
    mock_db.commit.assert_called_once()


def test_remove_admin_forbidden(api_client: TestClient) -> None:
    response = api_client.delete(
        f"/admins/{str(uuid4())}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "false"},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("customer_id", ("str", "123", str(uuid4()) + "a"))
def test_remove_admin_wrong_id(
    api_client: TestClient,
    customer_id: str,
) -> None:
    response = api_client.delete(
        f"/admins/{customer_id}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "true"},
    )
    assert response.status_code == 422


def test_remove_admin_not_found(api_client: TestClient, mock_db: MagicMock) -> None:
    customer_id = str(uuid4())

    def _get_customer(_: Any, user_id: UUID) -> None:
        assert str(user_id) == customer_id
        return None

    mock_db.get = _get_customer

    response = api_client.delete(
        f"/admins/{customer_id}",
        headers={"x-customer-id": str(uuid4()), "x-is-admin": "true"},
    )
    assert response.status_code == 404


def test_remove_last_admin(
    api_client: TestClient, mock_db: MagicMock, mocker: MockerFixture
) -> None:
    mock_admin = generate_random_db_customer(is_admin=True)

    def _get_customer(_: Any, user_id: UUID) -> Customer:
        assert user_id == mock_admin.id
        return mock_admin

    mock_return = mocker.Mock()

    def _scalars(query: Select[Customer.id]) -> mocker.Mock:
        assert str(query.compile()) == str(
            select(Customer.id).where(Customer.is_admin).compile()
        )
        return mock_return

    mock_db.get = _get_customer
    mock_db.scalars = _scalars
    mock_return.all.return_value = [mock_admin.id]

    response = api_client.delete(
        f"/admins/{str(mock_admin.id)}",
        headers={"x-customer-id": str(mock_admin.id), "x-is-admin": "true"},
    )
    assert response.status_code == 400


@pytest.mark.parametrize("was_admin", (True, False))
def test_remove_admin_success(
    api_client: TestClient, mock_db: MagicMock, was_admin: bool, mocker: MockerFixture
) -> None:
    mock_admin = generate_random_db_customer(is_admin=True)
    mock_user = generate_random_db_customer(is_admin=was_admin)

    def _get_customer(_: Any, user_id: UUID) -> Customer:
        assert user_id == mock_user.id
        return mock_user

    mock_return = mocker.Mock()

    def _scalars(query: Select[Customer.id]) -> mocker.Mock:
        assert str(query.compile()) == str(
            select(Customer.id).where(Customer.is_admin).compile()
        )
        return mock_return

    mock_db.get = _get_customer
    mock_db.scalars = _scalars
    mock_return.all.return_value = [mock_admin.id, mock_user.id]

    response = api_client.delete(
        f"/admins/{str(mock_user.id)}",
        headers={"x-customer-id": str(mock_admin.id), "x-is-admin": "true"},
    )
    assert response.status_code == 204

    assert mock_user.is_admin is False
    mock_db.commit.assert_called_once()
