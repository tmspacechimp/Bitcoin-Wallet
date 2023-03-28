from dataclasses import dataclass
from typing import Protocol


class IAuthenticateInteractor(Protocol):
    def authenticate(self, admin_key: str | None) -> bool:
        pass


@dataclass
class AuthenticateInteractor:
    authentication_key: str

    def authenticate(self, key: str | None) -> bool:
        if key is None:
            return False
        return key == self.authentication_key
