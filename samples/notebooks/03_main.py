from typing import List

import pandas as pd
from matplotlib.pylab import plt
import matplotlib.dates as mdates
from datetime import date
import pandas as pd
from demeter import Actuator, MarketInfo, TokenInfo, Strategy, ChainType
from demeter.uniswap import UniV3Pool, UniLpMarket
from demeter import MarketInfo
from demeter.broker import AccountStatus
from demeter.result import performance_metrics


def plotter(account_status_list: List[AccountStatus]):
    net_value_ts = [status.net_value for status in account_status_list]
    time_ts = [status.timestamp for status in account_status_list]
    plt.plot(time_ts, net_value_ts)
    plt.show()


def plot_position_return_decomposition(
    account_status: pd.DataFrame, price: pd.Series, market: MarketInfo
):
    fig, value_ax = plt.subplots()
    day = mdates.DayLocator(interval=2)

    price_ax = value_ax.twinx()
    price_ax.xaxis.set_major_locator(day)
    price_ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    value_ax.set_xlabel("time")
    value_ax.set_ylabel("value", color="g")
    price_ax.set_ylabel("price", color="b")

    net_value_ts = list(account_status.net_value)
    time_ts = list(account_status.index)
    price_ts = list(price)

    value_in_position = account_status[market.name]["net_value"]
    value_in_account = account_status["tokens"]["USDC"] + account_status["tokens"]["ETH"] * price

    value_ax.plot(time_ts, net_value_ts, "g-", label="net value")
    value_ax.plot(time_ts, value_in_position, "r-", label="value in get_position")
    value_ax.plot(time_ts, value_in_account, "b-", label="value in broker account")
    price_ax.plot(time_ts, price_ts, "y-", label="price")
    fig.legend()
    fig.show()


class ConstantIntervalStrategy(Strategy):
    def __init__(self, a=100):
        super().__init__()
        self.a = a

    def initialize(self):
        market: UniLpMarket = self.markets[market_key]
        init_price = market.market_status.data.price
        market.even_rebalance(init_price)  # rebalance all reserve token#
        # new_position(self, baseToken, quoteToken, usd_price_a, usd_price_b):
        # what is  base/quote "https://corporatefinanceinstitute.com/resources/knowledge/economics/currency-pair/"
        market.add_liquidity(init_price - self.a, init_price + self.a)
        super().__init__()


usdc = TokenInfo(name="usdc", decimal=6)  # declare  token0
eth = TokenInfo(name="eth", decimal=18)  # declare token1
pool = UniV3Pool(usdc, eth, 0.05, usdc)  # declare pool
market_key = MarketInfo("market1")

actuator = Actuator()  # declare actuator
broker = actuator.broker
market = UniLpMarket(market_key, pool)

broker.add_market(market)
broker.set_balance(usdc, 2000)
broker.set_balance(eth, 0)

actuator.strategy = ConstantIntervalStrategy(200)

market.data_path = "/Users/gnapsamuel/Documents/AMM/demeter/samples/data"
market.load_data(
    ChainType.polygon.name,
    "0x45dda9cb7c25131df268515131f647d726f50608",
    date(2023, 8, 13),
    date(2023, 8, 17),
)
actuator.set_price(market.get_price_from_data())
actuator.run()  # run test
print(
    {
        k: round(v, 5)
        for k, v in performance_metrics(
            actuator.account_status_df["net_value"],
            benchmark=actuator.account_status_df["price"]["ETH"],
        ).items()
    }
)

actuator.save_result(
    path="./result",  # save path
    account=True,  # save account status list as a csv file
    actions=True,  # save actions as a json file and a pickle file
)
