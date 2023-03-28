from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, auto
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Protocol

from fastapi import HTTPException

from app.core.clients.http import IHTTPClient, RequestsClient


class Currency(Enum):
    BITCOIN = auto()
    USD = auto()


class IRateService(Protocol):
    def get_rate(self, from_currency: Currency, to_currency: Currency) -> Decimal:
        pass


class IHTTPRateService(Protocol):
    def ping(self) -> bool:
        pass

    def get_rate(self, from_currency: Currency, to_currency: Currency) -> Decimal:
        pass


@dataclass
class HTTPRateService(IHTTPRateService):
    rate_base_url: str
    status_url: str
    http_client: IHTTPClient
    currency_mapper: MappingProxyType[Currency, str]
    rate_url_formatting_strategy: Callable[[str, str, str], str]
    rate_response_parsing_strategy: Callable[[Dict[str, Any] | List[Any]], Decimal]
    status_response_parsing_strategy: Callable[[Dict[str, Any] | List[Any]], bool]

    def get_rate(self, from_currency: Currency, to_currency: Currency) -> Decimal:
        url = self.rate_url_formatting_strategy(
            self.rate_base_url,
            self.currency_mapper[from_currency],
            self.currency_mapper[to_currency],
        )
        response = self.http_client.get(url)
        return self.rate_response_parsing_strategy(response)

    def ping(self) -> bool:
        response = self.http_client.get(self.status_url)
        return self.status_response_parsing_strategy(response)


bitfinex_mapper = MappingProxyType({Currency.BITCOIN: "BTC", Currency.USD: "USD"})


def bitfinex_rate_response_parser(response: Dict[str, Any] | List[Any]) -> Decimal:
    return Decimal(response[0])  # type: ignore


def appender(base_url: str, from_currency: str, to_currency: str) -> str:
    url = base_url + from_currency + to_currency
    return url


def bitfinex_status_parser(response: Dict[str, Any] | List[Any]) -> bool:
    return bool(response[0])  # type: ignore


@dataclass
class BitFinexRateService(HTTPRateService):
    rate_base_url: str = field(
        init=False, default="https://api.bitfinex.com/v2/ticker/t"
    )
    status_url: str = field(
        init=False, default="https://api-pub.bitfinex.com/v2/platform/status"
    )
    http_client: IHTTPClient = field(default_factory=RequestsClient)
    currency_mapper: MappingProxyType[Currency, str] = bitfinex_mapper
    rate_url_formatting_strategy: Callable[[str, str, str], str] = appender

    rate_response_parsing_strategy: Callable[
        [Dict[str, Any] | List[Any]], Decimal
    ] = bitfinex_rate_response_parser
    status_response_parsing_strategy: Callable[
        [Dict[str, Any] | List[Any]], bool
    ] = bitfinex_status_parser


kraken_mapper = MappingProxyType({Currency.BITCOIN: "btc", Currency.USD: "usd"})


def kraken_rate_response_parser(response: Dict[str, Any] | List[Any]) -> Decimal:
    return Decimal(response["result"]["XXBTZUSD"][0][0])  # type: ignore


def kraken_status_parser(response: Dict[str, Any] | List[Any]) -> bool:
    return response["result"]["status"] == "online"  # type: ignore


@dataclass
class KrakenFinexRateService(HTTPRateService):
    rate_base_url: str = field(
        init=False, default="https://api.bitfinex.com/v2/ticker/t"
    )
    status_url: str = field(
        init=False, default="https://api.kraken.com/0/public/SystemStatus"
    )
    http_client: IHTTPClient = field(default_factory=RequestsClient)
    currency_mapper: MappingProxyType[Currency, str] = field(
        init=False, default=kraken_mapper
    )
    rate_url_formatting_strategy: Callable[[str, str, str], str] = field(
        init=False, default=appender
    )
    rate_response_parsing_strategy: Callable[
        [Dict[str, Any] | List[Any]], Decimal
    ] = field(init=False, default=kraken_rate_response_parser)
    status_response_parsing_strategy: Callable[
        [Dict[str, Any] | List[Any]], bool
    ] = field(init=False, default=kraken_status_parser)


class SubstitutableHTTPRateService(IRateService):
    services: List[IHTTPRateService] = [BitFinexRateService(), KrakenFinexRateService()]

    def get_rate(self, from_currency: Currency, to_currency: Currency) -> Decimal:
        for service in self.services:
            if service.ping:  # type: ignore
                return service.get_rate(from_currency, to_currency)
        raise HTTPException(status_code=500, detail="Service unavailable")
