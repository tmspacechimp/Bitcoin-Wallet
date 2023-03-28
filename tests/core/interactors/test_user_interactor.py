from functools import cache
from sqlite3 import connect
from typing import Callable

import pytest

from app.core.interactors.users import UserInteractor
from app.core.models.req.user import CreateUserRequest
from app.core.models.resp.core_response import CoreStatus
from app.core.models.resp.user import CreateUserResponse
from app.infra.sqlite.users import UsersSqlRepository

key_generation_strategy: Callable[[str], str] = lambda s: s + "_key"


class TestCreateUser:
    @classmethod
    @pytest.fixture
    @cache
    def interactor(cls) -> UserInteractor:
        repository = UsersSqlRepository(connect(":memory:", check_same_thread=False))
        repository.create_user("test", "test_key")
        return UserInteractor(
            user_repository=repository,
            api_key_generation_strategy=key_generation_strategy,
        )

    def test_should_create_user(self, interactor: UserInteractor) -> None:
        good_email = "test_1"
        response = interactor.create_user(CreateUserRequest(email=good_email))
        assert response.status == CoreStatus.USER_CREATED
        assert response.response_content == CreateUserResponse(
            api_key=key_generation_strategy(good_email)
        )

    def test_should_fail_bad_email(self, interactor: UserInteractor) -> None:
        bad_email = "test"
        response = interactor.create_user(CreateUserRequest(email=bad_email))
        assert response.status == CoreStatus.EMAIL_ALREADY_IN_USE
        assert response.message == f"email: {bad_email} already in use"


class TestGetUserId:
    @classmethod
    @pytest.fixture
    @cache
    def interactor(cls) -> UserInteractor:
        repository = UsersSqlRepository(connect(":memory:", check_same_thread=False))
        repository.create_user("test", "test_key")
        return UserInteractor(
            user_repository=repository,
            api_key_generation_strategy=key_generation_strategy,
        )

    def test_should_get_id(self, interactor: UserInteractor) -> None:
        good_key = "test_key"
        response = interactor.get_user_id(api_key=good_key)
        assert response.status == CoreStatus.SUCCESSFUL_GET
        assert response.response_content == 1

    def test_should_fail_invalid_api_key(self, interactor: UserInteractor) -> None:
        bad_key = "bad_key"
        response = interactor.get_user_id(api_key=bad_key)
        assert response.status == CoreStatus.INVALID_API_KEY
        assert response.message == f"api_key: {bad_key} is invalid"
