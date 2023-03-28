from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar


class CoreStatus(Enum):
    # can be filled with different cases that all
    # eventually get mapped to http status codes
    SUCCESSFUL_GET = auto()
    SUCCESSFUL_POST = auto()
    EMAIL_ALREADY_IN_USE = auto()
    USER_CREATED = auto()
    INVALID_API_KEY = auto()
    INVALID_ADMIN_KEY = auto()
    UNSUCCESSFUL_GET = auto()
    UNSUCCESSFUL_POST = auto()
    INVALID_REQUEST = auto()
    WALLET_LIMIT_REACHED = auto()
    WALLET_ADDRESS_TAKEN = auto()
    WALLET_ADDRESS_NOT_FOUND = auto()
    WALLET_DOESNT_BELONG_TO_USER = auto()
    INSUFFICIENT_FUNDS = auto()


T = TypeVar("T")


@dataclass
class CoreResponse(Generic[T]):
    response_content: T
    status: CoreStatus = CoreStatus.SUCCESSFUL_GET
    message: str = ""
