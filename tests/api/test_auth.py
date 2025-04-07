from unittest.mock import MagicMock

import bcrypt
import pytest
from fastapi.testclient import TestClient

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

    mock_db.scalar.return_value = mock_user

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
    mock_db.scalar.return_value = None
    response = api_client.get("/auth", auth=("username", "password"))
    assert response.status_code == 401


@pytest.mark.parametrize("is_admin", (True, False))
def test_auth_wrong_password(
    api_client: TestClient, mock_db: MagicMock, is_admin: bool
) -> None:
    mock_user = generate_random_db_customer(is_admin=is_admin)
    mock_db.scalar.return_value = mock_user

    response = api_client.get("/auth", auth=(mock_user.username, "wrong-password"))
    assert response.status_code == 401
