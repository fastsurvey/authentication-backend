
from tests.conftest import get_content_dict, TEST_EMAIL_DOMAIN, \
    assert_jwt_account_response


TEST_ACCOUNT = {"email": "c" + TEST_EMAIL_DOMAIN, "password": "000000d!"}


def test_login(client):
    # Login with not-registered account
    response = client.post("/login/form", data=TEST_ACCOUNT)
    assert(response.status_code == 401)

    # Registered that account
    response = client.post("/register", data=TEST_ACCOUNT)
    assert(response.status_code == 200)

    # Login with registered account
    response = client.post("/login/form", data=TEST_ACCOUNT)
    assert(response.status_code == 200)

    # Check whether response has the right format
    content_dict = get_content_dict(response)
    assert_jwt_account_response(content_dict)

    # Try to get private data with invalid access_token
    response = client.get("/account", headers={
        "Authorization": "bearer 123"
    })
    assert(response.status_code == 401)

    # Try to get private data with valid access_token
    response = client.get("/account", headers={
        "Authorization": "bearer " + content_dict["jwt"]["access_token"]
    })
    assert(response.status_code == 200)
    content_dict = get_content_dict(response)
    assert(content_dict == {"email": TEST_ACCOUNT["email"], "email_verified": False})
