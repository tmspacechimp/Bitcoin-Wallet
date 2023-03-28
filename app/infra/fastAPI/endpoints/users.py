from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.facade import BitcoinWalletCore
from app.core.models.req.user import CreateUserRequest
from app.core.models.resp.core_response import CoreStatus
from app.core.models.resp.user import CreateUserResponse
from app.infra.fastAPI.dependables import get_core
from app.infra.fastAPI.endpoints.status_mappings import to_http

users_api: APIRouter = APIRouter()


@users_api.post("/users", responses={201: {}, 400: {}, 403: {}, 404: {}})
def create_user(
    request: CreateUserRequest,
    response: Response,
    core: BitcoinWalletCore = Depends(get_core),
) -> CreateUserResponse:
    core_response = core.create_user(request)
    if core_response.status != CoreStatus.USER_CREATED:
        raise HTTPException(to_http[core_response.status], detail=core_response.message)
    response.status_code = to_http[CoreStatus.USER_CREATED]
    return core_response.response_content
