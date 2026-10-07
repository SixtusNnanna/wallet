from decimal import Decimal
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from backend.api.dependencies import get_paystack_client
from backend.main import app
from backend.services.repayment import confirm_repayment_success



async def test_initate_repayment_success(
    client,
    repayment_setup,
    access_token_customer,
):
    response = await client.post(
        "/repayments/initiate",
        json={"amount": 10000},
        headers={
            "Authorization": access_token_customer
        }
        )
    assert response.status_code == 200
    body = response.json()
    assert "repayment_id" in body


async def test_amount_below_installment(
    client,
    repayment_setup,
    access_token_customer,
):
    response = await client.post(
        "/repayments/initiate",
        json={"amount": 100},
        headers={
                "Authorization": access_token_customer
        }
    )
    assert response.status_code == 409
    body = response.json()
    assert body["detail"] == "You can't repay amount below 566.67 "

@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_non_active_loan(mock_blist, client, access_token_customer):
    mock_blist.return_value = False
    response = await client.post(
            "/repayments/initiate",
            json={"amount": 10000},
            headers={
                "Authorization": access_token_customer
            }
        )
    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "No active loan, Not Found"


async def test_user_mismath(
    client,
    repayment_user_mismatch,
    access_token_customer
):
    response = await client.post(
        "/repayments/initiate",
        json={"amount": 10000},
        headers={
            "Authorization": access_token_customer
            }

        )
    body = response.json()
    assert response.status_code == 404
    assert body["detail"] == "Loan, Not Found"


@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_payment_reconcile_success(
    mock_blist,
    client,
    repayment,
    access_token,
):
    mock_blist.return_value = False
    mock_paystack = AsyncMock()
    mock_paystack.verify_transction.return_value = {
        "data": {
            "status": "success",
            "amount": int(repayment.amount * 100),
        }
    }
    app.dependency_overrides[get_paystack_client] = lambda: mock_paystack

    response = await client.post(
        f"/repayments/{repayment.id}/reconcile",
        headers={
            "Authorization": access_token
        }
        )
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Payment Reconciled"


@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_payment_reconcile_is_idempotent(
    mock_blist,
    client,
    repayment,
    access_token,
):
    mock_blist.return_value = False

    mock_paystack = AsyncMock()
    mock_paystack.verify_transction.return_value = {
        "data": {
            "status": "success",
            "amount": int(repayment.amount * 100),
        }
    }
    app.dependency_overrides[get_paystack_client] = lambda: mock_paystack

    response_1 = await client.post(
        f"/repayments/{repayment.id}/reconcile",
        headers={"Authorization": access_token}
    )

    assert response_1.status_code == 200

    response_2 = await client.post(
        f"/repayments/{repayment.id}/reconcile",
        headers={"Authorization": access_token}
    )
    assert response_2.status_code == 404
    assert "no pending repayment" in response_2.json()["detail"].lower()
    mock_paystack.verify_transction.assert_awaited_once()
