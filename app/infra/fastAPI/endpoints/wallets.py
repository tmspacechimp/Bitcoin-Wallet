from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.core.facade import BitcoinWalletCore
from app.core.models.resp.core_response import CoreStatus
from app.core.models.resp.wallet import WalletResponse
from app.infra.fastAPI.dependables import get_core
from app.infra.fastAPI.endpoints.status_mappings import to_http

wallets_api: APIRouter = APIRouter()


@wallets_api.post("/wallets", responses={201: {}, 400: {}, 403: {}, 404: {}})
def create_wallet(
    response: Response,
    api_key: str | None = Header(None),
    core: BitcoinWalletCore = Depends(get_core),
) -> WalletResponse:
    core_response = core.create_wallet(api_key)
    if core_response.status != CoreStatus.SUCCESSFUL_POST:
        raise HTTPException(to_http[core_response.status], detail=core_response.message)
    response.status_code = to_http[core_response.status]
    return core_response.response_content


@wallets_api.get("/wallets/{address}", responses={200: {}, 400: {}, 403: {}, 404: {}})
def get_wallet_balance(
    response: Response,
    address: str,
    api_key: str | None = Header(None),
    core: BitcoinWalletCore = Depends(get_core),
) -> WalletResponse:
    core_response = core.get_wallet_balance(api_key, address)
    if core_response.status != CoreStatus.SUCCESSFUL_GET:
        raise HTTPException(to_http[core_response.status], detail=core_response.message)
    response.status_code = to_http[core_response.status]
    return core_response.response_content
