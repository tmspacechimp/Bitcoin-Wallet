from dataclasses import dataclass


@dataclass
class StatisticsResponse:
    num_transaction: int
    profit_in_satoshi: int


BadStatisticsResponse = StatisticsResponse(0, 0)
