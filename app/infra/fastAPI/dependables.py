from starlette.requests import Request

from app.core.facade import BitcoinWalletCore


def get_core(request: Request) -> BitcoinWalletCore:
    core: BitcoinWalletCore = request.app.state.core
    return core
