import uuid
import pytest
from unittest.mock import AsyncMock, patch



SIGNUP_PAYLOAD = {
    "full_name":"test user",
    "email": "testuser@xample.com",
    "phone": "+2347047382932",
    "address": "No 14 Bassey",
    "password": "H@ty1232"
}




@patch("backend.services.user.sendmail")
async def test_successfull_sign_up(mock_sendmail, client):
    response = await client.post("/auth/signup", json=SIGNUP_PAYLOAD)
    assert response.status_code in (200, 201)
    body = response.json()
    assert body["email"] == SIGNUP_PAYLOAD["email"]
    assert body["full_name"] == SIGNUP_PAYLOAD["full_name"]
    assert body["role"] == "customer"
    assert "password" not in body
    assert "password_hash" not in body
    mock_sendmail.delay.assert_called_once()


@patch("backend.services.user.sendmail")
async def test_email_duplication(mock_mail, client):
    first = await client.post(
        "/auth/signup", json=SIGNUP_PAYLOAD
    )
    second = await client.post(
        "/auth/signup", json=SIGNUP_PAYLOAD
    )
    body = second.json()
    assert second.status_code == 400
    assert body["detail"] == "User Already Exists"
    mock_mail.delay.assert_called_once()


@patch("backend.services.user.sendmail")
async def test_success_full_login(mock_mail, client):
    await client.post(
        "/auth/signup", json=SIGNUP_PAYLOAD
    )
    response = await client.post(
        "/auth/token", data={
            "username": "testuser@xample.com",
            "password": "H@ty1232"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    mock_mail.delay.assert_called_once()


async def test_signup_invalid_phone_rejected(client):
    payload = {**SIGNUP_PAYLOAD, "email": f"badphone-{uuid.uuid4().hex[:8]}@example.com", "phone": "not-a-phone"}

    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 422



async def test_signup_weak_password_rejected(client):
    payload = {**SIGNUP_PAYLOAD, "email": f"weak-{uuid.uuid4().hex[:8]}@example.com", "password": "short"}

    response = await client.post("/auth/signup", json=payload)
    assert response.status_code == 422


@patch("backend.services.user.sendmail")
async def test_login_wrong_password_rejected(mock_mail, client):
    signup_payload = {**SIGNUP_PAYLOAD, "email": f"wrongpw-{uuid.uuid4().hex[:8]}@example.com"}
    await client.post("/auth/signup", json=signup_payload)

    response = await client.post(
        "/auth/token",
        data={"username": signup_payload["email"], "password": "TotallyWrongPassword1!"},
    )

    assert response.status_code == 401
    mock_mail.delay.assert_called_once()


async def test_login_nonexistent_user_leaks_existence(client):
    response = await client.post(
        "/auth/token",
        data={"username": "definitely-not-registered@example.com", "password": "whatever123"},
    )
    assert response.status_code == 404


@patch("backend.services.user.sendmail.delay")
async def test_password_reset_code_request_existing_user(mock_sendmail, client):
    signup_payload = {**SIGNUP_PAYLOAD}
    await client.post("/auth/signup", json=signup_payload)
    response = await client.post("/auth/password-reset-code", json={
        "email": "testuser@xample.com"
    })

    assert response.status_code == 200
    assert mock_sendmail.call_count == 2

@patch("backend.services.user.sendmail.delay")
async def test_password_reset_code_request_non_existing_user(mock_sendmail, client):
    signup_payload = {**SIGNUP_PAYLOAD}
    await client.post("/auth/signup", json=signup_payload)
    response = await client.post("/auth/password-reset-code", json={"email": "nonexistentuser@xample.com"})

    assert response.status_code == 200
    mock_sendmail.assert_called_once()


@patch("backend.services.user.get_verifcation_code", new_callable=AsyncMock)
async def test_invalid_code_reject(mock_get_code, client):
    fake_user_id = str(uuid.uuid4())
    mock_get_code.return_value = fake_user_id

    response = await client.post(
        "auth/reset-password-code",
        json={
            "code": "000000",
            "password": "Nna@1305",
            "confirm_password": "Nna@1305"
        }
        )
    assert response.status_code in (400, 401, 404)
    mock_get_code.assert_called_once_with("000000")


async def test_unmatched_password(client):
    response = await client.post(
        "auth/reset-password-code",
        json={
            "code": "000000",
            "password": "Nna@1307",
            "confirm_password": "Nna@1305"
        }
        )
    assert response.status_code == 422












