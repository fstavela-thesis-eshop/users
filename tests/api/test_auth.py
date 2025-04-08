from unittest.mock import MagicMock

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Select
from sqlalchemy import select

from db.models import Customer
from tests.helpers import generate_random_db_customer


@pytest.mark.parametrize("is_admin", (True, False))
def test_auth_success(
    api_client: TestClient, mock_db: MagicMock, is_admin: bool
) -> None:
    mock_user = generate_random_db_customer(is_admin=is_admin)
    password = "super-secret"
    mock_user.password = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    def _scalar(query: Select[Customer]) -> Customer:
        assert str(query.compile()) == str(
            select(Customer).where(Customer.username == mock_user.username).compile()
        )
        return mock_user

    mock_db.scalar = _scalar

    response = api_client.get("/auth", auth=(mock_user.username, password))

    assert response.status_code == 200
    assert response.headers["x-customer-id"] == str(mock_user.id)
    assert response.headers["x-is-admin"] == str(is_admin)

    response_json = response.json()
    assert isinstance(response_json, dict)
    assert len(response_json.keys()) == 2
    assert set(response_json.keys()) == {"id", "is_admin"}
    assert response_json["id"] == str(mock_user.id)
    assert response_json["is_admin"] == is_admin


def test_auth_wrong_username(api_client: TestClient, mock_db: MagicMock) -> None:
    def _scalar(query: Select[Customer]) -> None:
        assert str(query.compile()) == str(
            select(Customer).where(Customer.username == "my-user").compile()
        )
        return None

    mock_db.scalar = _scalar

    response = api_client.get("/auth", auth=("my-user", "password"))
    assert response.status_code == 401


@pytest.mark.parametrize("is_admin", (True, False))
def test_auth_wrong_password(
    api_client: TestClient, mock_db: MagicMock, is_admin: bool
) -> None:
    mock_user = generate_random_db_customer(is_admin=is_admin)

    def _scalar(query: Select[Customer]) -> Customer:
        assert str(query.compile()) == str(
            select(Customer).where(Customer.username == mock_user.username).compile()
        )
        return mock_user

    mock_db.scalar = _scalar

    response = api_client.get("/auth", auth=(mock_user.username, "wrong-password"))
    assert response.status_code == 401
