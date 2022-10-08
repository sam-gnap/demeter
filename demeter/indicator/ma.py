from pandas import Timedelta

from .._typing import ZelosError, DECIMAL_ZERO
import pandas as pd
from enum import Enum
from decimal import Decimal


class TimeUnitEnum(Enum):
    minute = 1
    hour = 60
    day = 60 * 24


def simple_moving_average(data: pd.Series, n=5, unit=TimeUnitEnum.hour) -> pd.Series:
    if data.size < 2:
        raise ZelosError("not enough data for simple_moving_average")
    timespan: Timedelta = data.index[1] - data.index[0]
    if timespan.seconds % 60 != 0:
        return ZelosError("no seconds is allowed")
    span_in_minute = timespan.total_seconds() / 60
    if unit.value % span_in_minute != 0:
        raise ZelosError(f"ma span is {n}{unit.name}, but data span is {span_in_minute}minute, cannot divide exactly")
    real_n = n * int(unit.value / span_in_minute)
    if data.size < real_n:
        raise ZelosError("not enough data for simple_moving_average")

    sum = Decimal(0)

    row_id = 0

    sma_array = []
    for index, value in data.iteritems():
        if row_id < real_n - 1:
            sma_array.append(DECIMAL_ZERO)
            sum += value
        elif row_id == real_n - 1:
            sum += value
            sma_array.append(sum / real_n)
        else:
            # data_before_n = data.iloc[row_id + 1 - real_n:row_id + 1]
            # sma_array.append(data_before_n.mean())
            sum -= data.iloc[row_id - real_n]
            sum += value
            sma_array.append(sum / real_n)

        row_id += 1

    return pd.Series(data=sma_array, index=data.index)
