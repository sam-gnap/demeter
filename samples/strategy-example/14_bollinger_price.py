import math
import pandas as pd
from datetime import date, timedelta

import demeter
from demeter import (
    TokenInfo,
    Actuator,
    Strategy,
    ChainType,
    PeriodTrigger,
    realized_volatility,
    simple_moving_average,
    MarketInfo,
    RowData,
)
from demeter.uniswap import UniV3Pool, UniLpMarket
from demeter import PriceTrigger

c = 2


class BollingerPrice(Strategy):

    def initialize(self):
        """
        This function is called before main loop is executed.
        you can prepare data, or register trigger here
        """

        # Add a simple moving average line for backtesting data. In backtesting,
        # we will add/remove liquidity according to this line.
        self.add_column(
            market_key,
            "sma_1d",
            simple_moving_average(self.data[market_key].price, window=timedelta(hours=16)),
        )
        self.add_column(
            market_key,
            "volatility_1d",
            realized_volatility(self.data[market_key].price, timedelta(days=1), timedelta(days=1)),
        )
        # Register a trigger, every day, we split both assets into two shares of equal value
        self.current_lower_price = 2400
        self.current_upper_price = 2700

        # Register the PriceTrigger
        self.triggers.append(
            PriceTrigger(condition=self.is_price_out_of_range, do=self.handle_out_of_range_price)
        )

        self.markets.default.even_rebalance(self.data[market_key].iloc[0]["price"])

    def is_price_out_of_range(self, prices: pd.Series) -> bool:
        # 2396 and 2929
        if self.current_lower_price is None or self.current_upper_price is None:
            return False
        current_price = prices[eth.name]
        return current_price < self.current_lower_price or current_price > self.current_upper_price

    def handle_out_of_range_price(self, row_data: RowData):
        print(
            f"Price out of range. Current price: {row_data.prices[eth.name]}, Range: {self.current_lower_price} - {self.current_upper_price}"
        )
        lp_market: UniLpMarket = self.broker.markets[market_key]

        # Remove all liquidity
        lp_market.remove_all_liquidity()

        # Recalculate the range and add liquidity again
        self.work(row_data)

    def work(self, row_data: RowData):
        lp_market: UniLpMarket = self.broker.markets[market_key]
        lp_row_data = row_data.market_status[market_key]

        if len(lp_market.positions) > 0:
            lp_market.remove_all_liquidity()

        lp_market.even_rebalance(row_data.prices[eth.name])

        if math.isnan(lp_row_data.volatility_1d):
            return

        limit = c * float(row_data.prices[eth.name]) * lp_row_data.volatility_1d

        self.current_lower_price = lp_row_data.sma_1d - limit
        self.current_upper_price = lp_row_data.sma_1d + limit

        if self.broker.assets[market.base_token].balance > 0:
            lp_market.add_liquidity(self.current_lower_price, self.current_upper_price)
        else:
            lp_market.add_liquidity(self.current_lower_price, self.current_upper_price)


if __name__ == "__main__":
    demeter.Formats.global_num_format = ".4g"  # change out put formats here

    usdc = TokenInfo(name="usdc", decimal=6)  # declare  token0
    eth = TokenInfo(name="eth", decimal=18)  # declare token1
    pool = UniV3Pool(usdc, eth, 0.05, usdc)  # declare pool
    market_key = MarketInfo("lp")

    actuator = Actuator()  # declare actuator
    broker = actuator.broker
    market = UniLpMarket(market_key, pool)

    broker.add_market(market)
    broker.set_balance(usdc, 5000)
    broker.set_balance(eth, 0)

    actuator.strategy = BollingerPrice()
    market.data_path = "/Users/gnapsamuel/Documents/AMM/demeter-fetch/sample-data"
    market.load_data(
        ChainType.ethereum.name,
        "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        date(2024, 8, 15),
        date(2024, 9, 1),
    )
    actuator.set_price(market.get_price_from_data())
    actuator.run()  # run test
