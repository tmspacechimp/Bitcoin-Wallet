import sqlite3

import pytest

from app.infra.sqlite.users import UsersSqlRepository


@pytest.fixture
def repository() -> UsersSqlRepository:
    return UsersSqlRepository(sqlite3.connect(":memory:", check_same_thread=False))


def test_create_user(repository: UsersSqlRepository) -> None:
    assert repository.create_user("test", "test_key")


def test_get_id(repository: UsersSqlRepository) -> None:
    repository.create_user("test", "test_key")
    assert repository.get_user_id("test_key") != -1
    assert repository.get_user_id("test_key") == 1


def test_user_exists_with_email(repository: UsersSqlRepository) -> None:
    repository.create_user("test", "test_key")
    assert repository.user_exists_with_email("test")
    assert not repository.user_exists_with_email("test1")
