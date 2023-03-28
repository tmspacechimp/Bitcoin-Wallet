from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.core.facade import BitcoinWalletCore
from app.core.models.resp.core_response import CoreStatus
from app.core.models.resp.statistics import StatisticsResponse
from app.infra.fastAPI.dependables import get_core
from app.infra.fastAPI.endpoints.status_mappings import to_http

statistics_api: APIRouter = APIRouter()


@statistics_api.get("/statistics", responses={200: {}, 400: {}, 403: {}, 404: {}})
def get_statistics(
    response: Response,
    admin_key: str | None = Header(None),
    core: BitcoinWalletCore = Depends(get_core),
) -> StatisticsResponse:
    core_response = core.get_statistics(admin_key)
    if core_response.status != CoreStatus.SUCCESSFUL_GET:
        raise HTTPException(to_http[core_response.status], detail=core_response.message)
    response.status_code = to_http[core_response.status]
    return core_response.response_content
