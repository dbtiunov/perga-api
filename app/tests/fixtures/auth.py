import pytest

from app.models.user import User
from app.services.auth_utils import generate_password_hash, create_access_token
from app.tests.const import TEST_USERNAME, TEST_EMAIL, TEST_PASSWORD


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user for authentication tests"""
    user = User(
        username=TEST_USERNAME,
        email=TEST_EMAIL,
        hashed_password=generate_password_hash(TEST_PASSWORD),
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()

    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}
