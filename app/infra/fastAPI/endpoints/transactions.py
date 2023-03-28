from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.core.facade import BitcoinWalletCore
from app.core.models.req.transaction import TransactionRequest
from app.core.models.resp.core_response import CoreStatus
from app.core.models.resp.transaction import GetTransactionsResponse
from app.infra.fastAPI.dependables import get_core
from app.infra.fastAPI.endpoints.status_mappings import to_http

transactions_api: APIRouter = APIRouter()


@transactions_api.post("/transactions", responses={201: {}, 400: {}, 403: {}, 404: {}})
def make_transaction(
    request: TransactionRequest,
    response: Response,
    api_key: str | None = Header(None),
    core: BitcoinWalletCore = Depends(get_core),
) -> str:
    core_response = core.make_transaction(api_key, request)
    if core_response.status != CoreStatus.SUCCESSFUL_POST:
        raise HTTPException(to_http[core_response.status], detail=core_response.message)
    response.status_code = to_http[core_response.status]
    return core_response.message


@transactions_api.get("/transactions", responses={200: {}, 400: {}, 403: {}, 404: {}})
def get_transactions(
    response: Response,
    api_key: str | None = Header(None),
    core: BitcoinWalletCore = Depends(get_core),
) -> GetTransactionsResponse:
    core_response = core.get_transactions(api_key)
    if core_response.status != CoreStatus.SUCCESSFUL_GET:
        raise HTTPException(to_http[core_response.status], detail=core_response.message)
    response.status_code = to_http[core_response.status]
    return core_response.response_content


@transactions_api.get(
    "/wallets/{address}/transaction", responses={200: {}, 400: {}, 403: {}, 404: {}}
)
def get_transactions_for_wallet(
    response: Response,
    address: str,
    api_key: str | None = Header(None),
    core: BitcoinWalletCore = Depends(get_core),
) -> GetTransactionsResponse:
    core_response = core.get_transactions_for_wallet(api_key, address)
    if core_response.status != CoreStatus.SUCCESSFUL_GET:
        raise HTTPException(to_http[core_response.status], detail=core_response.message)
    response.status_code = to_http[core_response.status]
    return core_response.response_content
