from unittest.mock import patch

SIGNUP_PAYLOAD = {
    "full_name": "test2 user",
    "email": "testuser1@xample.com",
    "phone": "+2347037382932",
    "address": "No 14 Bassey",
    "is_verified": True,
    "role": "admin",
    "password": "H@ty1232"
}
loan_payload = {
  "status": "active",
  "repayment_frequency": "monthly",
  "start_date": "2026-08-24T19:03:32.800922Z",
  "due_date": "2026-08-24T19:03:32.800942Z",
  "end_date": "2026-08-24T19:03:32.800953Z",
  "principal": 100000
}


async def test_create_loan(
    client,
    access_token,
    customer_user,
):
    response = await client.post(
        "/loans/",
        json={
            **loan_payload, "user_id": str(customer_user.id)
        },
        headers={
            "Authorization": access_token
        }


        )
    assert response.status_code in (200, 201)
    body = response.json()
    assert "balance" in body


@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_create_loan_for_non_existent_user(
    mock_blacklisted,
    client,
    access_token,
):
    mock_blacklisted.return_value = False
    response = await client.post(
            "/loans/",
            json={
                **loan_payload,
                "user_id": "b4398b73-2baa-4dd4-a38e-033c2073f4d8"
            },
            headers={
                "Authorization": access_token
            }

            )
    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "User, Not Found"


@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_loan_create_by_non_admin(
    mock_blist,
    client,
    access_token_customer,
    admin_user,
):
    mock_blist.return_value = False
    response = await client.post(
        "/loans/",
        json={
            **loan_payload, "user_id": str(admin_user.id)
            },
        headers={
                "Authorization": access_token_customer
                }
        )
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "You do not have permission to access this resource"


@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_admin_creating_loan_for_once_self(
    mock_blist,
    client,
    admin_user,
    access_token,
):
    mock_blist.return_value = False
    response = await client.post(
        "/loans/",
        json={
                **loan_payload, "user_id": str(admin_user.id)
            },
        headers={
                "Authorization": access_token
            }

                    )
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "You cannot Create Loan for yourself"

@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_current_loan(mock_blist, loan ,client, access_token_customer):
    mock_blist.return_value = False
    response = await client.get(
        "/loans/me/current",
        headers={"Authorization": access_token_customer}
        )
    assert response.status_code == 200
    body = response.json()
    assert loan.balance == body["balance"]
    assert str(loan.id) == body["id"]
    assert loan.status.value == "active"


@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_current_pending_loan(mock_blist, paid_off_laon, client, access_token_customer):
    mock_blist.return_value = False
    response = await client.get(
            "/loans/me/current",
            headers={"Authorization": access_token_customer}
            )
    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "No active loan, Not Found"


@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_loans_with_staff_previlages_by_staff(
        mock_blist,
        loan,
        client,
        access_token,
        ):
    mock_blist.return_value = False
    response = await client.get(
                "/loans/staff",
                headers={"Authorization": access_token}
               )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1


@patch("backend.api.dependencies.is_jti_blacklisted")
async def test_loans_with_staff_previlages_by_non_staff(
        mock_blist,
        loan,
        client,
        access_token_customer,
        ):
    mock_blist.return_value = False
    response = await client.get(
                "/loans/staff",
                headers={"Authorization": access_token_customer}
               )
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "You do not have permission to access this resource"










