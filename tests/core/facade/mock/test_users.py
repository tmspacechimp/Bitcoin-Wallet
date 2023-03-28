from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest

from app.core.facade import BitcoinWalletCore
from app.core.models.req.user import CreateUserRequest
from app.core.models.resp.core_response import CoreResponse, CoreStatus
from app.core.models.resp.user import CreateUserResponse


@pytest.fixture
def bitcoin_wallet_core() -> BitcoinWalletCore:
    transactions_interactor = MagicMock()
    user_interactor = MagicMock()
    wallet_interactor = MagicMock()
    authenticate_interactor = MagicMock()
    commission_calculator = MagicMock()

    return BitcoinWalletCore(
        transactions_interactor,
        user_interactor,
        wallet_interactor,
        authenticate_interactor,
        commission_calculator,
    )


_successful_response = CoreResponse(
    response_content=CreateUserResponse("1"),
    status=CoreStatus.USER_CREATED,
    message="user successfully created",
)

_unsuccessful_response = CoreResponse(
    response_content=CreateUserResponse(""),
    status=CoreStatus.EMAIL_ALREADY_IN_USE,
    message="email already in use",
)

_different_response = CoreResponse(
    response_content=CreateUserResponse("0"),
    status=CoreStatus.USER_CREATED,
    message="user successfully created",
)


# user tested for successful response
def test_create_user_successful(bitcoin_wallet_core: BitcoinWalletCore) -> None:
    request = CreateUserRequest(email="MockMail")
    bitcoin_wallet_core.user_interactor = MagicMock()
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "create_user",
        return_value=_successful_response,
    ) as mock_create_user:
        result = bitcoin_wallet_core.create_user(request)
        assert asdict(result) == asdict(_successful_response)
        mock_create_user.assert_called_once_with(request)


# user tested for unsuccessful response
def test_unsuccessful_response(bitcoin_wallet_core: BitcoinWalletCore) -> None:
    request = CreateUserRequest(email="MockMail")
    bitcoin_wallet_core.user_interactor = MagicMock()
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "create_user",
        return_value=_unsuccessful_response,
    ) as mock_create_user:
        result = bitcoin_wallet_core.create_user(request)
        assert asdict(result) == asdict(_unsuccessful_response)
        mock_create_user.assert_called_once_with(request)


# user tested for different response
def test_different_response(bitcoin_wallet_core: BitcoinWalletCore) -> None:
    request = CreateUserRequest(email="MockMail")
    bitcoin_wallet_core.user_interactor = MagicMock()
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "create_user",
        return_value=_different_response,
    ) as mock_create_user:
        result = bitcoin_wallet_core.create_user(request)
        assert asdict(result) != asdict(_successful_response)
        assert asdict(result) == asdict(_different_response)
        mock_create_user.assert_called_once_with(request)
