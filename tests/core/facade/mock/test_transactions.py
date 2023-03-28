from dataclasses import asdict
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.core.facade import BitcoinWalletCore
from app.core.models.req.transaction import TransactionRequest
from app.core.models.resp.core_response import CoreResponse, CoreStatus
from app.core.models.resp.wallet import WalletResponse


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


def test_make_transaction_invalid_api_key(
    bitcoin_wallet_core: BitcoinWalletCore,
) -> None:
    api_key = None
    request = TransactionRequest(
        from_address="address1", to_address="address2", amount_in_satoshi=100
    )
    invalid_result = CoreResponse(None, CoreStatus.INVALID_API_KEY)
    user_id_response = CoreResponse(None, CoreStatus.INVALID_API_KEY)
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "get_user_id",
        return_value=user_id_response,
    ) as mock_user_id:
        result = bitcoin_wallet_core.make_transaction(api_key, request)
        assert asdict(result) == asdict(invalid_result)
        mock_user_id.assert_called_once_with(api_key)


def test_make_transaction_invalid_wallet(
    bitcoin_wallet_core: BitcoinWalletCore,
) -> None:
    api_key = "None"
    request = TransactionRequest(
        from_address="address1", to_address="address2", amount_in_satoshi=100
    )
    ownership_violation_result = CoreResponse(
        None, CoreStatus.WALLET_DOESNT_BELONG_TO_USER
    )
    user_id_response = CoreResponse(1, CoreStatus.SUCCESSFUL_GET)
    wallet_id_response = CoreResponse(20, CoreStatus.SUCCESSFUL_GET)
    check_ownership_response = CoreResponse(
        False, CoreStatus.WALLET_DOESNT_BELONG_TO_USER
    )
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "get_user_id",
        return_value=user_id_response,
    ) as mock_user_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "get_wallet_id",
        return_value=wallet_id_response,
    ) as mock_wallet_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_belongs_to_user",
        return_value=check_ownership_response,
    ) as mock_ownership:
        result = bitcoin_wallet_core.make_transaction(api_key, request)
        assert asdict(result) == asdict(ownership_violation_result)
        mock_user_id.assert_called_once_with(api_key)
        mock_wallet_id.assert_called_once_with("address1")
        mock_ownership.assert_called_once_with(
            wallet_id_response.response_content, user_id_response.response_content
        )


def test_make_transaction_invalid_address(
    bitcoin_wallet_core: BitcoinWalletCore,
) -> None:
    api_key = "None"
    request = TransactionRequest(
        from_address="address1", to_address="address2", amount_in_satoshi=100
    )
    user_id_response = CoreResponse(1, CoreStatus.SUCCESSFUL_GET)
    wallet_id_response = CoreResponse(20, CoreStatus.SUCCESSFUL_GET)
    check_ownership_response = CoreResponse(True, CoreStatus.SUCCESSFUL_GET)
    invalid_wallet_response = CoreResponse(None, CoreStatus.INVALID_REQUEST)
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "get_user_id",
        return_value=user_id_response,
    ) as mock_user_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "get_wallet_id",
        return_value=wallet_id_response,
    ) as mock_wallet_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_belongs_to_user",
        return_value=check_ownership_response,
    ) as mock_ownership, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_exists",
        return_value=invalid_wallet_response,
    ) as mock_existence:
        result = bitcoin_wallet_core.make_transaction(api_key, request)
        assert asdict(result) == asdict(invalid_wallet_response)
        mock_user_id.assert_called_once_with(api_key)
        mock_wallet_id.assert_called_once_with("address1")
        mock_ownership.assert_called_once_with(
            wallet_id_response.response_content, user_id_response.response_content
        )
        mock_existence.assert_called_once_with("address2")


def test_make_transaction_not_enough_balance(
    bitcoin_wallet_core: BitcoinWalletCore,
) -> None:
    api_key = "None"
    request = TransactionRequest(
        from_address="address1", to_address="address2", amount_in_satoshi=100
    )
    user_id_response = CoreResponse(1, CoreStatus.SUCCESSFUL_GET)
    wallet_id_response = CoreResponse(20, CoreStatus.SUCCESSFUL_GET)
    check_ownership_response = CoreResponse(True, CoreStatus.SUCCESSFUL_GET)
    valid_wallet_response = CoreResponse(19, CoreStatus.SUCCESSFUL_GET)
    wallet_balance_response = CoreResponse(
        WalletResponse("address1", 10, Decimal(2)), CoreStatus.SUCCESSFUL_GET
    )
    no_balance_response = CoreResponse(
        None, CoreStatus.INSUFFICIENT_FUNDS, "insufficient funds"
    )
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "get_user_id",
        return_value=user_id_response,
    ) as mock_user_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "get_wallet_id",
        return_value=wallet_id_response,
    ) as mock_wallet_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_belongs_to_user",
        return_value=check_ownership_response,
    ) as mock_ownership, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_exists",
        return_value=valid_wallet_response,
    ) as mock_existence, patch.object(
        bitcoin_wallet_core.commission_calculator,
        "get_commission",
        return_value=10,
    ) as mock_commission, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "get_wallet_balance",
        return_value=wallet_balance_response,
    ) as mock_balance:
        result = bitcoin_wallet_core.make_transaction(api_key, request)
        assert asdict(result) == asdict(no_balance_response)
        mock_user_id.assert_called_once_with(api_key)
        mock_wallet_id.assert_called_once_with("address1")
        mock_ownership.assert_called_once_with(
            wallet_id_response.response_content, user_id_response.response_content
        )
        mock_existence.assert_called_once_with("address2")
        mock_commission.assert_called_once_with(
            user_id_response.response_content,
            wallet_id_response.response_content,
            valid_wallet_response.response_content,
            request.amount_in_satoshi,
        )
        mock_balance.assert_called_once_with("address1")


def test_make_transaction_unsuccessful(bitcoin_wallet_core: BitcoinWalletCore) -> None:
    api_key = "None"
    request = TransactionRequest(
        from_address="address1", to_address="address2", amount_in_satoshi=100
    )
    user_id_response = CoreResponse(1, CoreStatus.SUCCESSFUL_GET)
    wallet_id_response = CoreResponse(20, CoreStatus.SUCCESSFUL_GET)
    check_ownership_response = CoreResponse(True, CoreStatus.SUCCESSFUL_GET)
    valid_wallet_response = CoreResponse(19, CoreStatus.SUCCESSFUL_GET)
    wallet_balance_response = CoreResponse(
        WalletResponse("address1", 1000, Decimal(2)), CoreStatus.SUCCESSFUL_GET
    )
    unsuccessful_response = CoreResponse(None, CoreStatus.UNSUCCESSFUL_POST)
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "get_user_id",
        return_value=user_id_response,
    ) as mock_user_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "get_wallet_id",
        return_value=wallet_id_response,
    ) as mock_wallet_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_belongs_to_user",
        return_value=check_ownership_response,
    ) as mock_ownership, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_exists",
        return_value=valid_wallet_response,
    ) as mock_existence, patch.object(
        bitcoin_wallet_core.commission_calculator,
        "get_commission",
        return_value=10,
    ) as mock_commission, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "get_wallet_balance",
        return_value=wallet_balance_response,
    ) as mock_balance, patch.object(
        bitcoin_wallet_core.transactions_interactor,
        "create",
        return_value=unsuccessful_response,
    ) as mock_transaction:
        result = bitcoin_wallet_core.make_transaction(api_key, request)
        assert asdict(result) == asdict(unsuccessful_response)
        mock_user_id.assert_called_once_with(api_key)
        mock_wallet_id.assert_called_once_with("address1")
        mock_ownership.assert_called_once_with(
            wallet_id_response.response_content, user_id_response.response_content
        )
        mock_existence.assert_called_once_with("address2")
        mock_commission.assert_called_once_with(
            user_id_response.response_content,
            wallet_id_response.response_content,
            valid_wallet_response.response_content,
            request.amount_in_satoshi,
        )
        mock_balance.assert_called_once_with("address1")
        mock_transaction.assert_called_with(
            wallet_id_response.response_content,
            valid_wallet_response.response_content,
            request.amount_in_satoshi,
            10,
        )


def test_make_transaction_successful(bitcoin_wallet_core: BitcoinWalletCore) -> None:
    api_key = "None"
    request = TransactionRequest(
        from_address="address1", to_address="address2", amount_in_satoshi=100
    )
    user_id_response = CoreResponse(1, CoreStatus.SUCCESSFUL_GET)
    wallet_id_response = CoreResponse(20, CoreStatus.SUCCESSFUL_GET)
    check_ownership_response = CoreResponse(True, CoreStatus.SUCCESSFUL_GET)
    valid_wallet_response = CoreResponse(19, CoreStatus.SUCCESSFUL_GET)
    wallet_balance_response = CoreResponse(
        WalletResponse("address1", 1000, Decimal(2)), CoreStatus.SUCCESSFUL_GET
    )
    successful_response = CoreResponse(None, CoreStatus.SUCCESSFUL_POST)
    update_balance_response = CoreResponse(None, CoreStatus.SUCCESSFUL_POST)
    with patch.object(
        bitcoin_wallet_core.user_interactor,
        "get_user_id",
        return_value=user_id_response,
    ) as mock_user_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "get_wallet_id",
        return_value=wallet_id_response,
    ) as mock_wallet_id, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_belongs_to_user",
        return_value=check_ownership_response,
    ) as mock_ownership, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "check_wallet_exists",
        return_value=valid_wallet_response,
    ) as mock_existence, patch.object(
        bitcoin_wallet_core.commission_calculator,
        "get_commission",
        return_value=10,
    ) as mock_commission, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "get_wallet_balance",
        return_value=wallet_balance_response,
    ) as mock_balance, patch.object(
        bitcoin_wallet_core.transactions_interactor,
        "create",
        return_value=successful_response,
    ) as mock_transaction, patch.object(
        bitcoin_wallet_core.wallet_interactor,
        "update_balance",
        return_value=update_balance_response,
    ) as mock_update:
        result = bitcoin_wallet_core.make_transaction(api_key, request)
        assert asdict(result) == asdict(successful_response)
        mock_user_id.assert_called_once_with(api_key)
        mock_wallet_id.assert_called_once_with("address1")
        mock_ownership.assert_called_once_with(
            wallet_id_response.response_content, user_id_response.response_content
        )
        mock_existence.assert_called_once_with("address2")
        mock_commission.assert_called_once_with(
            user_id_response.response_content,
            wallet_id_response.response_content,
            valid_wallet_response.response_content,
            request.amount_in_satoshi,
        )
        mock_balance.assert_called_with("address2")
        mock_transaction.assert_called_once_with(
            wallet_id_response.response_content,
            valid_wallet_response.response_content,
            request.amount_in_satoshi,
            10,
        )
        # am not checking both address call would be good
        mock_update.assert_called_with("address2", 1100)
