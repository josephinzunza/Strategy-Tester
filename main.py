from datamodels import MarketData
from dynamic_enums import AvailableStudies
from enums import AverageType, FrequencyType, PeriodType
from schwabapi import SchwabAPIClient

import numpy as np
import pandas as pd
import studies
import time
import utils


def main():
    #aapl_md = utils.get_market_data("AAPL", FrequencyType.Daily, 1)
    #spy_md = utils.get_market_data("SPY", FrequencyType.Daily, 1)
    #print(studies.RealRelativeStrength.calculate(aapl_md, spy_md, 20)[:21])
    print(AvailableStudies.AverageTrueRange.name)

if __name__ == "__main__":
    main()