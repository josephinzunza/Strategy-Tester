from enum import Enum

class AverageType(Enum):
    Simple = 0
    Exponential = 1
    Weighted = 2
    Wilders = 3
    Hull = 4
    
class FrequencyType(Enum):
    Minute = 0
    Daily = 1
    Weekly = 2
    Monthly = 3

class PeriodType(Enum):
    Day = 0
    Month = 1
    Year = 2
    Ytd = 3

class OpeningPositionEffect(Enum):
    BuyToOpen = 0
    SellToOpen = 1

class PriceType(Enum):
    Open    = 0
    High    = 1
    Low     = 2
    Close   = 3
    Volume  = 4
    HL2     = 5
    HLC3    = 6
    OHLC4   = 7 