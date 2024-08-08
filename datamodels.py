import numpy as np
import pandas as pd
import os

from datetime import datetime
from enums import FrequencyType
from typing import Union


class MarketData:

    def __init__(self, symbol : str, candles : Union[list, pd.DataFrame], frequency_type : FrequencyType, frequency : int) -> None:
        self.symbol = symbol

        if (isinstance(candles, pd.DataFrame)):
            self.candles = candles
        elif(isinstance(candles, list)):
            self.candles = self.__candles_to_dataframe(candles)
        self.frequency_type = frequency_type
        self.frequency = frequency
        
    def __candles_to_dataframe(self, candles : dict) -> pd.DataFrame:
        length = len(candles)
        open = np.empty(shape=length, dtype=np.float64)
        high = np.empty(shape=length, dtype=np.float64)
        low = np.empty(shape=length, dtype=np.float64)
        close = np.empty(shape=length, dtype=np.float64)
        volume = np.empty(shape=length, dtype=np.int64)
        date = np.empty(shape=length, dtype=np.int64)
        for i in range(length):
            candle = candles[i]
            open[i] = candle["open"]
            high[i] = candle["high"]
            low[i] = candle["low"]
            close[i] = candle["close"]
            volume[i] = candle["volume"]
            date[i] =  candle["datetime"]
        df = pd.DataFrame({"open":open, "high":high, "low":low, "close":close, "volume":volume, "datetime":date.astype("datetime64[ms]")})
        df.set_index("datetime", inplace=True)
        df = df.tz_localize("UTC").tz_convert("US/Pacific")
        return df
    
    def get_path(frequency_type : FrequencyType, frequency : int) -> str:
        fname = "json\\"
        if (frequency_type == FrequencyType.Minute):
            fname += f"Intraday\\{frequency}Min\\"
        else:
            fname += frequency_type.name
        return fname
    
    def save_to_json(self, path : str = None):
        if (path is None):
            path = MarketData.get_path(self.frequency_type, self.frequency)
        if (not os.path.exists(path)):
            os.makedirs(path)
        fname = path + f"\\{self.symbol}.json"
        self.candles.to_json(fname, orient="index", indent=4, date_format="iso", date_unit="ms")

        

            