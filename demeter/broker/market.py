import logging
from decimal import Decimal

import pandas as pd

from ._typing import BaseAction, MarketBalance, MarketStatus
from .. import DECIMAL_0
from ..data_line import Lines

DEFAULT_DATA_PATH = "./data"


class Market:
    """
    note: only get properties are allow in this base class
    """

    def __init__(self,
                 data: Lines = None,
                 data_path=DEFAULT_DATA_PATH):
        self._data: Lines = data
        self.broker = None
        self._record_action_callback = None
        self.data_path: str = data_path
        self.logger = logging.getLogger(__name__)
        self._market_status = MarketStatus(None)

    @property
    def net_value(self) -> Decimal:
        return Decimal(0)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if isinstance(value, Lines):
            self._data = value
        else:
            raise ValueError()

    def record_action(self, action: BaseAction):
        if self._record_action_callback is not None:
            self._record_action_callback(action)

    # region for subclass to override
    def check_asset(self):
        pass

    def update(self):
        pass

    @property
    def market_status(self):
        return self._market_status

    @market_status.setter
    def market_status(self, data):
        self._market_status = data

    def get_market_balance(self, prices: pd.Series) -> MarketBalance:
        return MarketBalance(DECIMAL_0)
    # endregion
