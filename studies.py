from datamodels import MarketData
from enums import AverageType, PriceType
import pandas as pd
import numpy as np
from utils import get_price

class Study:

    def __init__(self, market_data : MarketData, displace : int = 0) -> None:
        self.market_data = market_data
        self.displace = displace
        self.values = None

class AverageTrueRange(Study):

    def __init__(self, market_data : MarketData,
                 length : int = 14,
                 average_type : AverageType = AverageType.Wilders,
                 displace : int = 0) -> None:
        self.length = length
        self.average_type = average_type
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()

    def __calculate(self) -> None:
        self.values = AverageTrueRange.calculate(self.market_data, self.length, self.average_type, self.displace)

    def calculate(market_data : MarketData, length : int, average_type : AverageType, displace : int = 0) -> pd.Series:
        if (average_type == AverageType.Simple):
            return SimpleMovingAverage.calculate(TrueRange.calculate(market_data.candles), length).shift(displace)
        if (average_type == AverageType.Exponential):
            return ExponentialMovingAverage.calculate(TrueRange.calculate(market_data.candles), length).shift(displace)
        if (average_type == AverageType.Weighted):
            return WeightedMovingAverage.calculate(TrueRange.calculate(market_data.candles), length).shift(displace)
        if (average_type == AverageType.Wilders):
            return WildersMovingAverage.calculate(TrueRange.calculate(market_data.candles), length).shift(displace)

class BollingerBands(Study):
    
    def __init__(self, market_data : MarketData,
                 price : PriceType = PriceType.Close,
                 length : int = 20,
                 std_devs : float = 2.0,
                 average_type : AverageType = AverageType.Simple,
                 displace : int = 0) -> None:
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()

class DonchianChannels(Study):
     
    def __init__(self, market_data : MarketData,
                length : int = 20,
                displace : int = 0) -> None:
        self.length = length
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()

    def __calculate(self) -> None:
        data = get_price(self.market_data.candles, self.priceType)
        self.values = SimpleMovingAverage.calculate(data, self.length, self.displace)
    
    def calculate(dataframe : pd.DataFrame, length : int, displace : int = 0) -> pd.DataFrame:
        lowerChannel = dataframe["low"].rolling(length).min().shift(displace)
        upperChannel = dataframe["high"].rolling(length).max().shift(displace)
        middleChannel = (lowerChannel + upperChannel) / 2
        dict = {
            "lower": lowerChannel,
            "middle": middleChannel,
            "upper": upperChannel
        }
        return pd.DataFrame(dict)

class ExponentialMovingAverage(Study):
    
    def __init__(self, market_data : MarketData,
                 length : int = 20,
                 price_type : PriceType = PriceType.Close,
                 displace : int = 0) -> None:
        self.length = length
        self.price_type: price_type
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()

    def __calculate(self) -> None:
        data = get_price(self.market_data.candles, self.priceType)
        self.values = SimpleMovingAverage.calculate(data, self.length, self.displace)
    
    def calculate(column : pd.Series, length : int, displace : int = 0) -> pd.Series:
        return column.ewm(alpha=2/(length + 1)).mean().shift(displace)

class PercentR(Study):

    def __init__(self, market_data : MarketData,
                 length : int = 14,
                 displace : int = 0) -> None:
        self.length = length
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()
    
    def __calculate(self) -> None:
        self.values = PercentR.calculate(self.market_data, self.length, self.displace)

    def calculate(market_data : MarketData, length : int, displace : int = 0) -> pd.Series:
        highest = market_data.candles["high"].rolling(length).max()
        divisor = highest - market_data.candles["low"].rolling(length).min()
        return (100 - (100 * (highest - market_data.candles["close"]) / divisor)).shift(displace)

class RealRelativeStrength(Study):

    def __init__(self, market_data : MarketData,
                 compared_market_data : MarketData,
                 length : int,
                 displace : int = 0) -> None:
        self.compared_market_data = compared_market_data
        self.length = length
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()

    def __calculate(self) -> None:
        self.values = RealRelativeStrength.calculate(self.market_data, self.compared_market_data, self.length, self.displace)

    def calculate(market_data : MarketData, compared_market_data : MarketData, length : int, displace : int = 0) -> pd.Series:
        rolling_move = market_data.candles["close"].diff(length)
        compared_rolling_move = compared_market_data.candles["close"].diff(length)
        rolling_atr = AverageTrueRange.calculate(market_data, length, AverageType.Wilders)
        compared_atr = AverageTrueRange.calculate(compared_market_data, length, AverageType.Wilders)
        power_index = compared_rolling_move / compared_atr
        expected_move = power_index * rolling_atr
        diff = rolling_move - expected_move
        return (diff / rolling_atr).shift(displace)

class SimpleMovingAverage(Study):
    
    def __init__(self, market_data : MarketData,
                 length : int = 20,
                 price_type : PriceType = PriceType.Close,
                 displace : int = 0) -> None:
        self.length = length
        self.price_type = price_type
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate

    def __calculate(self) -> None:
        data = get_price(self.market_data.candles, self.price_type)
        self.values = SimpleMovingAverage.calculate(data, self.length, self.displace)
    
    def calculate(column : pd.Series, length : int, displace : int = 0) -> pd.Series:
        return column.rolling(length).mean().shift(displace)

class TrueRange(Study):

    def __init__(self, market_data : MarketData, displace : int = 0) -> None:
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()
    
    def __calculate(self) -> None:
        self.values = TrueRange.calculate(self.market_data, self.displace)
    
    def calculate(dataframe : pd.DataFrame, displace : int = 0) -> pd.Series:
        high = dataframe["high"]
        low = dataframe["low"]
        previous_close = dataframe["close"].shift(periods=1)
        data = pd.DataFrame({"tr0": high - low, "tr1": abs(high - previous_close), "tr2": abs(low - previous_close)})
        data.set_index(dataframe.index)
        true_range = data.max(axis=1)
        return true_range.shift(displace)

class WeightedMovingAverage(Study):

    def __init__(self, market_data : MarketData,
                 length : int = 20,
                 price_type : PriceType = PriceType.Close,
                 displace : int = 0) -> None:
        self.length = length
        self.price_type: price_type
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()

    def __calculate(self) -> None:
        data = get_price(self.market_data.candles, self.priceType)
        self.values = WeightedMovingAverage.calculate(data, self.length, self.displace)

    def calculate(column : pd.Series, length : int, displace : int = 0) -> pd.Series:
        weights = np.arange(length) + 1
        weights_sum = length * (length + 1) / 2
        swv = np.lib.stride_tricks.sliding_window_view(column.values.flatten(), window_shape=length)
        sw = (swv*weights).sum(axis=1) / weights_sum
        nans = np.empty(shape=(length - 1,))
        nans[:] = np.nan
        return pd.Series(np.concatenate([nans, sw]), index=column.index).shift(displace)

class WildersMovingAverage(Study):

    def __init__(self, market_data : MarketData,
                 length : int = 20,
                 price_type : PriceType = PriceType.Close,
                 displace : int = 0) -> None:
        self.length = length
        self.price_type: price_type
        Study.__init__(self, market_data, displace)
        self.calculate = self.__calculate()

    def __calculate(self) -> None:
        data = get_price(self.market_data.candles, self.priceType)
        self.values = WeightedMovingAverage.calculate(data, self.length, self.displace)

    def calculate(column : pd.Series, length : int, displace : int = 0) -> pd.Series:
        return column.ewm(alpha=1.0/length).mean().shift(displace)