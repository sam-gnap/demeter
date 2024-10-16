from datetime import timedelta

import numpy as np
import pandas as pd
from pandas._typing import TimedeltaConvertibleTypes, Axis

from .common import get_real_n


def simple_moving_average(
    data: pd.Series | pd.DataFrame,
    window: timedelta = timedelta(hours=5),
    min_periods: int | None = None,
    center: bool = False,
    win_type: str | None = None,
    on: str | None = None,
    closed: str | None = None,
    method: str = "single",
) -> pd.Series:
    """
    calculate simple moving average, Note: window is based on time span

    docs for other params, see https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.rolling.html

    :param data: data
    :type data: Series
    :param window: window width
    :type window: timedelta
    :return: simple moving average data
    :rtype: Series

    """

    return data.rolling(
        window=get_real_n(data, window),
        min_periods=min_periods,
        center=center,
        win_type=win_type,
        on=on,
        closed=closed,
        method=method,
    ).mean()


def exponential_moving_average(
    data: pd.Series | pd.DataFrame,
    com: float | None = None,
    span: float | None = None,
    halflife: float | TimedeltaConvertibleTypes | None = None,
    alpha: float | None = None,
    min_periods: int | None = 0,
    adjust: bool = True,
    ignore_na: bool = False,
    times: str | np.ndarray | pd.DataFrame | pd.Series | None = None,
    method: str = "single",
):
    """
    Calculate exponential moving average, just a shortcut for pandas.evm().mean()

    Parameters:
    -----------
    data : pd.Series or pd.DataFrame
        The input data for which to calculate the EMA.
    com : float, optional
        Specify decay in terms of center of mass, α = 1 / (1 + com).
    span : float, optional
        Specify decay in terms of span, α = 2 / (span + 1).
    halflife : float, TimedeltaConvertibleTypes, optional
        Specify decay in terms of half-life, α = 1 - exp(log(0.5) / halflife).
    alpha : float, optional
        Specify smoothing factor directly, 0 < α ≤ 1.
    min_periods : int, default 0
        Minimum number of observations in window required to have a value.
    adjust : bool, default True
        Divide by decaying adjustment factor in beginning periods to account for imbalance in relative weightings.
    ignore_na : bool, default False
        Ignore missing values when calculating weights.
    times : str, np.ndarray, pd.DataFrame, pd.Series, optional
        Time-based index to use in EWM calculation.
    method : str, default 'single'
        Method to use for EWM calculation ('single' or 'table').

    docs for params, see: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.ewm.html
    """
    return data.ewm(
        com=com,
        span=span,
        halflife=halflife,
        alpha=alpha,
        min_periods=min_periods,
        adjust=adjust,
        ignore_na=ignore_na,
        times=times,
        method=method,
    ).mean()


def volume_weighted_moving_average(
    data: pd.Series | pd.DataFrame,
    window: timedelta = timedelta(hours=5),
    min_periods: int | None = None,
    center: bool = False,
    win_type: str | None = None,
    on: str | None = None,
    closed: str | None = None,
    method: str = "single",
) -> pd.Series:
    """
    calculate volume weighted moving average

    docs for other params, see https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Series.rolling.html

    :param data: Pandas datarame
    :type data: Series
    :param window: window width
    :type window: timedelta
    :return: volume weighted moving average
    :rtype: Series

    """
    volume = abs(data["netAmount0"].astype(np.float64))
    price = data["price"].astype(np.float64)
    price_volume = volume * price
    rolling_price_volume = price_volume.rolling(
        window=get_real_n(price_volume, window),
        min_periods=min_periods,
        center=center,
        win_type=win_type,
        on=on,
        closed=closed,
        method=method,
    ).sum()
    rolling_volume = volume.rolling(
        window=get_real_n(volume, window),
        min_periods=min_periods,
        center=center,
        win_type=win_type,
        on=on,
        closed=closed,
        method=method,
    ).sum()
    return rolling_price_volume / rolling_volume
