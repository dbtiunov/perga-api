import pytest

from app.models.user import User
from app.services.auth_utils import generate_password_hash


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create a test user for authentication tests"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=generate_password_hash("password123"),
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()

    test_db.refresh(user)
    return user
