from datamodels import MarketData
from enums import FrequencyType, PeriodType, PriceType
from io import StringIO
from schwabapi import SchwabAPIClient

import json
import os.path
import pandas as pd


def get_price(dataframe : pd.DataFrame, priceType : PriceType) -> pd.Series:
    if (priceType == PriceType.Close):
        return dataframe["close"]
    if (priceType == PriceType.High):
        return dataframe["high"]
    if (priceType == PriceType.Low):
        return dataframe["low"]
    if (priceType == PriceType.Open):
        return dataframe["open"]
    if (priceType == PriceType.HL2):
        return (dataframe["high"] + dataframe["low"]) / 2
    if (priceType == PriceType.HLC3):
        return (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3
    if (priceType == PriceType.HL2):
        return (dataframe["open"] + dataframe["high"] + dataframe["low"] + dataframe["close"]) / 4
    if (priceType == PriceType.Volume):
        return dataframe["volume"]

def get_market_data(symbol : str,
                    frequency_type : FrequencyType,
                    frequency : int,
                    get_fresh_data : bool = False) -> MarketData:
    path = MarketData.get_path(frequency_type, frequency) 
    if (get_fresh_data is False):
        fname = path + f"\\{symbol}.json"
        if (not os.path.isfile(fname)):
            get_fresh_data = True
        else:
            with open(fname, "r") as file:
                market_data = MarketData(symbol, pd.read_json(StringIO(file.read()), orient="index", date_unit="ms"), frequency_type, frequency)
                market_data.candles.index = pd.to_datetime(market_data.candles.index)
                return market_data
    else:
        client = SchwabAPIClient()
        if (frequency_type == FrequencyType.Minute):
            period_type = PeriodType.Day
            period = 10 # 10 days ago
            if (frequency != 1 or frequency != 5 or frequency != 10 or frequency != 15 or frequency != 30):
                frequency = 5 # 5 min frequency as default
        elif (frequency_type == FrequencyType.Daily):
            frequency = 1
            period_type = PeriodType.Year
            period = 5 # 5 years
        elif (frequency_type == FrequencyType.Weekly):
            frequency = 1
            period_type = PeriodType.Year
            period = 5 # 5 years
        elif (frequency_type == FrequencyType.Monthly):
            frequency = 1
            period_type = PeriodType.Year
            period = 10 # 10 years
        # Get market data without extended hours
        market_data = client.get_price_history(symbol,
                                               period_type,
                                               period, frequency_type,
                                               frequency,
                                               start_date=None,
                                               end_date=None,
                                               need_extended_hours_data=False)
        market_data.save_to_json(path=path)
        return market_data

def load_dynamic_enums() -> None:
    with open("studies.py", "r") as file:
        lines = file.readlines()
        study_list = []
        for line in lines:
            study_name_index = line.find("class ")
            if (study_name_index >= 0): # Class name was found
                study_name_index += 6 # Start looking after 'class ' substring
                end_index = line.find('(', study_name_index)
                if (end_index < 0):
                    continue
                study_list.append(line[study_name_index:end_index])
    enum_template = """from enum import Enum

class AvailableStudies(Enum):
\t{enum_body}"""

    enum_body = ""
    for i in range(len(study_list)):
        enum_body += study_list[i] + " = " + str(i) + "\n\t"
    
    enum_template = enum_template.format(enum_body=enum_body)
    with open("dynamic_enums.py", "w") as file:
        file.write(enum_template)

