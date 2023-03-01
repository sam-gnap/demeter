from decimal import Decimal
from typing import Dict

import pandas as pd

from ._typing import Asset, TokenInfo, AccountStatus, MarketDict, AssetDict
from .market import Market
from .._typing import DemeterError, UnitDecimal
from ..utils import get_formatted_from_dict, get_formatted_predefined, STYLE, \
    float_param_formatter


class Broker:
    def __init__(self, allow_negative_balance=False, record_action_callback=None):
        self.allow_negative_balance = allow_negative_balance
        self._assets: AssetDict[Asset] = AssetDict()
        self._markets: MarketDict[Market] = MarketDict()
        self._record_action_callback = record_action_callback

    # region properties

    @property
    def markets(self) -> MarketDict[Market]:
        return self._markets

    @property
    def assets(self) -> AssetDict[Asset]:
        return self._assets

    # endregion

    def __str__(self):
        return "assets: " + ",".join([f"({v})" for k, v in self._assets.items()]) + \
            "; markets: " + ",".join([f"({v})" for k, v in self.markets.items()])

    def add_market(self, market: Market):
        """
        Set a new market to broker,
        User should initialize market before set to broker(Because there are too many initial parameters)
        :param market_info:
        :type market_info:
        :param market:
        :type market:
        :return:
        :rtype:
        """
        if market.market_info in self._markets:
            raise DemeterError("market has exist")
        self._markets[market.market_info] = market
        market.broker = self
        market._record_action_callback = self._record_action_callback

    @float_param_formatter
    def add_to_balance(self, token: TokenInfo, amount: Decimal | float):
        """
        set initial balance for token

        :param token: which token to set
        :type token: TokenInfo
        :param amount: balance, eg: 1.2345
        :type amount: Decimal | float
        """
        if token in self._assets:
            asset: Asset = self._assets[token]
        else:
            asset: Asset = self.__add_asset(token)
        asset.add(amount)
        return asset

    @float_param_formatter
    def set_balance(self, token: TokenInfo, amount: Decimal | float):
        asset: Asset = self.__add_asset(token)
        asset.balance = amount
        return asset

    @float_param_formatter
    def subtract_from_balance(self, token: TokenInfo, amount: Decimal | float):
        if token in self._assets:
            asset: Asset = self._assets[token]
            asset.sub(amount, allow_negative_balance=self.allow_negative_balance)
        else:
            if self.allow_negative_balance:
                asset: Asset = self.__add_asset(token)
                asset.balance = 0 - amount
            else:
                raise DemeterError(f"{token.name} doesn't exist in assets dict")
        return asset

    def __add_asset(self, token: TokenInfo) -> Asset:
        self._assets[token] = Asset(token, 0)
        return self._assets[token]

    def get_token_balance(self, token: TokenInfo):
        if token in self.assets:
            return self._assets[token].balance
        else:
            raise DemeterError(f"{token.name} doesn't exist in assets dict")

    def get_token_balance_with_unit(self, token: TokenInfo):
        return UnitDecimal(self.get_token_balance(token), token.name)

    def get_account_status(self, prices: pd.Series | Dict[str, Decimal], timestamp=None) -> AccountStatus:
        account_status = AccountStatus(timestamp=timestamp)
        for k, v in self.markets.items():
            account_status.market_status[k] = v.get_market_balance(prices)
        account_status.market_status.set_default_key(self.markets.get_default_key())
        for k, v in self.assets.items():
            account_status.asset_balances[k] = v.balance
        asset_sum = sum([v * prices[k.name] for k, v in account_status.asset_balances.items()])
        market_sum = sum([v.net_value for v in account_status.market_status.values()])
        account_status.net_value = asset_sum + market_sum
        return account_status

    def formatted_str(self):
        str_to_print = get_formatted_predefined("Broker", STYLE["header1"]) + "\n"

        str_to_print += get_formatted_predefined("Asset amounts", STYLE["header2"]) + "\n"
        balances = {}
        for asset in self._assets.values():
            balances[asset.name] = asset.balance
        str_to_print += get_formatted_from_dict(balances) + "\n"
        str_to_print += get_formatted_predefined("Markets", STYLE["header2"]) + "\n"
        for market in self._markets.values():
            str_to_print += market.formatted_str() + "\n"
        return str_to_print
        # get_formatted_from_dict({
        #     "price": self.price.to_str(),
        #     "fee": self.fee.to_str(),
        #     "balance": f"{self.base_balance_after.to_str()}(-{self.base_change.to_str()}), {self.quote_balance_after.to_str()}(+{self.quote_change.to_str()})"
        # })
        # for market in self.broker.markets.values():
        #
        # return "Assets/n" + \
        #
        #     "assets: " + ",".join([f"({v})" for k, v in self._assets.items()]) + \
        #     "; markets: " + ",".join([f"({v})" for k, v in self.markets.items()])
