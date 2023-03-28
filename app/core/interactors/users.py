from dataclasses import dataclass, field
from hashlib import sha256
from typing import Callable, Protocol

from app.core.constants.constants import KEY_FOR_API_KEY_GEN
from app.core.models.req.user import CreateUserRequest
from app.core.models.resp.core_response import CoreResponse, CoreStatus
from app.core.models.resp.user import CreateUserResponse


class IUsersRepository(Protocol):
    def create_user(self, email: str, api_key: str) -> bool:
        pass

    def user_exists_with_email(self, email: str) -> bool:
        pass

    def get_user_id(self, api_key: str) -> int:
        pass


class IUsersInteractor(Protocol):
    def create_user(
        self, request: CreateUserRequest
    ) -> CoreResponse[CreateUserResponse]:
        pass

    def get_user_id(self, api_key: str | None) -> CoreResponse[int]:
        pass


def _sha_256_using_hardcoded_key(email: str) -> str:
    return sha256(f"{email}~{KEY_FOR_API_KEY_GEN}".encode()).hexdigest()


@dataclass
class UserInteractor:
    user_repository: IUsersRepository
    api_key_generation_strategy: Callable[[str], str] = field(
        default=_sha_256_using_hardcoded_key
    )

    def create_user(
        self, request: CreateUserRequest
    ) -> CoreResponse[CreateUserResponse]:
        if self._user_exists_by_email(request.email):
            return CoreResponse(
                response_content=CreateUserResponse(""),
                status=CoreStatus.EMAIL_ALREADY_IN_USE,
                message=f"email: {request.email} already in use",
            )

        api_key = self.api_key_generation_strategy(request.email)
        self.user_repository.create_user(request.email, api_key)
        return CoreResponse(
            response_content=CreateUserResponse(api_key=api_key),
            status=CoreStatus.USER_CREATED,
        )

    def _user_exists_by_email(self, email: str) -> bool:
        return self.user_repository.user_exists_with_email(email)

    def get_user_id(self, api_key: str | None) -> CoreResponse[int]:
        if api_key is None:
            return self._get_could_not_authenticate_response(api_key)
        user_id = self.user_repository.get_user_id(api_key=api_key)
        if user_id == -1:
            return self._get_could_not_authenticate_response(api_key)
        return CoreResponse(response_content=user_id, status=CoreStatus.SUCCESSFUL_GET)

    @classmethod
    def _get_could_not_authenticate_response(
        cls, api_key: str | None
    ) -> CoreResponse[int]:
        return CoreResponse(
            response_content=-1,
            status=CoreStatus.INVALID_API_KEY,
            message=f"api_key: {api_key} is invalid" or "api_key not present",
        )
