import pytest
import sqlite3
import uuid
import os
from database import init_db, create_user, verify_user, get_user_by_username, DB_NAME

@pytest.fixture(autouse=True)
def setup_teardown():
    init_db()
    yield
    
def test_create_and_verify_user():
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "SecurePassword123!"

    # 1. Create User
    success = create_user(username, email, password)
    assert success is True, "Failed to create user"

    # 2. Verify User with Correct Password
    user = verify_user(username, password)
    assert user is not None, "Failed to verify user with correct credentials"
    assert user['username'] == username
    assert 'id' in user

    # 3. Verify User with Incorrect Password
    user_wrong_pass = verify_user(username, "WrongPassword!")
    assert user_wrong_pass is None, "Should not verify with incorrect password"

    # 4. Verify Non-existent User
    non_existent = verify_user("nobody_here", "password")
    assert non_existent is None, "Should not verify a non-existent user"

def test_duplicate_user_creation():
    username = f"duplicate_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "SecurePassword123!"

    # Create the user successfully the first time
    success1 = create_user(username, email, password)
    assert success1 is True

    # Attempt to create the same user again
    success2 = create_user(username, email, password)
    assert success2 is False, "Should fail to create a duplicate user"

def test_get_user_by_username():
    username = f"lookup_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "SecurePassword123!"

    create_user(username, email, password)

    user = get_user_by_username(username)
    assert user is not None
    assert user['username'] == username
    assert user['email'] == email
    
    missing_user = get_user_by_username("does_not_exist")
    assert missing_user is None
