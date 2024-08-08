from dynamic_enums import AvailableStudies
from enums import AverageType, FrequencyType, OpeningPositionEffect, PriceType
from typing import Union
from utils import get_market_data

import json
import numpy as np
import pandas as pd
import studies

class Strategy:

    def __init__(self, file_name) -> None:
        self.main_symbols_list = [] # Holds the list of symbols used to test the strategy (for multi-symbol testing)
        self.current_main_symbol_index = None
        self.main_frequency = None
        self.main_frequency_type = None
        self.market_data_list = []
        self.studies_list = []
        self.desired_column = {}
        self.opening_position_effect = None
        self.opening_condition_str = None
        self.closing_condition_str = None
        self.initial_balance = None
        self.process_dict(file_name) # Get the strategy values from JSON file
        self.opening_indices = self.evaluate_expression(self.opening_condition_str)
        self.closing_indices = self.evaluate_expression(self.closing_condition_str)

    def process_dict(self, file_name) -> None:
        # Open file as dictionary
        with open(file_name, "r") as file:
            strategy_dict = json.load(file)
        
        # Get market data list
        data_list = strategy_dict["marketData"]
        self.main_symbols_list = data_list[0]
        self.main_symbols_list = self.main_symbols_list["symbol"]
        self.main_symbols_list = [x.strip() for x in data_list[0]["symbol"].split(",")] # Split comma-separated list and remove extra spaces
        # Check if the symbols list is a filename
        current_symbol = self.main_symbols_list[0]
        print(type(current_symbol))
        test = current_symbol[-4:].lower()
        if len(self.main_symbols_list) == 1 and len(self.main_symbols_list[0]) > 4 and self.main_symbols_list[0][-4:].lower() == ".txt":
            with open(self.main_symbols_list[0], "r") as file:
                # Get the lines in the file and put them into the symbols list
                self.main_symbols_list = [x.strip() for x in file.readlines()]
        self.main_frequency = data_list[0]["frequency"]
        self.main_frequency_type = FrequencyType[data_list[0]["frequencyType"]]
        market_data = get_market_data(self.main_symbols_list[0],
                                      self.main_frequency_type,
                                      self.main_frequency,
                                      True)
        self.market_data_list.append(market_data)
        self.current_main_symbol_index = 0
        for index in range(1, len(data_list)):
            data = data_list[index]
            market_data = get_market_data(data["symbol"],
                                          FrequencyType[data["frequencyType"]],
                                          data["frequency"],
                                          True)
            self.market_data_list.append(market_data)
        # Get studies list
        for study in strategy_dict["studies"]:
            study_name = study["name"]
            params = study["params"]
            params["marketDatas"] = []
            # Turn the market data IDs the study uses to an actual list in params
            for index in params["marketDataIds"]:
                params["marketDatas"].append(self.market_data_list[index])
            self.studies_list.append(Strategy.__get_study(study_name, params))
            # If this is a study with multiple columns, then the "desiredColumn" entry must exist in the dictionary
            if "desiredColumn" in study:
                self.desired_column[study["id"]] = study["desiredColumn"]
        pos_effect_str = strategy_dict["opening"]["type"]
        self.opening_position_effect = OpeningPositionEffect[pos_effect_str]
        self.opening_condition_str = strategy_dict["opening"]["condition"]
        self.closing_condition_str = strategy_dict["closing"]["condition"]
        self.initial_balance = float(strategy_dict["initialBalance"])
    

    def __get_study(name : str,
                    params : dict) -> studies.Study:
        study_type = AvailableStudies[name]
        if study_type == AvailableStudies.AverageTrueRange:
            study = studies.AverageTrueRange(params["marketDatas"][0],
                                             params["length"],
                                             AverageType[params["averageType"]],
                                             params["displace"])
        elif study_type == AvailableStudies.BollingerBands:
            study = studies.BollingerBands(params["marketDatas"][0],
                                           PriceType[params["price"].capitalize()],
                                           params["length"],
                                           params["stdDevs"],
                                           AverageType[params["averageType"]],
                                           params["displace"])
        elif study_type == AvailableStudies.DonchianChannels:
            study = studies.DonchianChannels(params["marketDatas"][0],
                                             params["length"],
                                             params["displace"])
        elif study_type == AvailableStudies.ExponentialMovingAverage:
            study = studies.ExponentialMovingAverage(params["marketDatas"][0],
                                                     params["length"],
                                                     PriceType[params["price"].capitalize()],
                                                     params["displace"])
        elif study_type == AvailableStudies.PercentR:
            study = studies.PercentR(params["marketDatas"][0],
                                     params["length"],
                                     params["displace"])
        elif study_type == AvailableStudies.RealRelativeStrength:
            study = studies.RealRelativeStrength(params["marketDatas"][0],
                                                 params["marketDatas"][1],
                                                 params["length"],
                                                 params["displace"])
        elif study_type == AvailableStudies.SimpleMovingAverage:
            study = studies.SimpleMovingAverage(params["marketDatas"][0],
                                                params["length"],
                                                PriceType[params["price"].capitalize()],
                                                params["displace"])
        elif study_type == AvailableStudies.TrueRange:
            study = studies.TrueRange(params["marketDatas"][0],
                                      params["displace"])
        elif study_type == AvailableStudies.WeightedMovingAverage:
            study = studies.WeightedMovingAverage(params["marketDatas"][0],
                                                  params["length"],
                                                  PriceType[params["price"].capitalize()],
                                                  params["displace"])
        elif study_type == AvailableStudies.WildersMovingAverage:
            study = studies.WildersMovingAverage(params["marketDatas"][0],
                                                  params["length"],
                                                  PriceType[params["price"].capitalize()],
                                                  params["displace"])
        else:
            raise NotImplementedError(f"Study {study_type.name} has not been implemented.")
        return study

    # Indicates the value of precedence of operators, from largest to smallest
    def __precedence(operator : str) -> int:
        if operator == "*" or operator == "/":
            return 5
        elif operator == "+" or operator == "-":
            return 4
        elif (operator == "<" or operator == "<=" or
            operator == ">" or operator == ">=" or
            operator == "crosses-above" or operator == "crosses-below"):
            return 3
        elif operator == "=" or operator == "!=":
            return 2
        elif operator == "&" or operator == "and":
            return 1
        elif operator == "|" or operator == "or":
            return 0
        else:
            raise NotImplementedError(f"Operator '{operator}' has not been implemented.")

    def __apply_operator(value1 : Union[pd.Series, float],
                value2 : Union[pd.Series, float],
                operator : str) -> pd.Series:
        if operator == "+":
            return value1 + value2
        elif operator == "-":
            return value1 - value2
        elif operator == "*":
            return value1 * value2
        elif operator == "/":
            return value1 / value2
        elif operator == ">":
            return value1 > value2
        elif operator == ">=":
            return value1 >= value2
        elif operator == "=":
            return value1 == value2
        elif operator == "!=":
            return value1 != value2
        elif operator == "<=":
            return value1 <= value2
        elif operator == "<":
            return value1 < value2
        elif operator == "|" or operator == "or":
            return value1 | value2
        elif operator == "&" or operator == "and":
            return value1 & value2
        elif operator == "crosses-above":
            # In this case value2 must be a pandas Series
            # A constant crossing above a series is the same as the series crossing below the constant
            if type(value1) == float or type(value1) == int:
                prev_value2 = value2.shift(1)
                return (prev_value2 >= value1) & (value2 < value1)
            # In this case value1 must be a pandas Series
            elif type(value2) == float or type(value2) == int:
                prev_value1 = value1.shift(1)
                return (prev_value1 <= value2) & (prev_value1 > value2)
            # In this case a pandas.Series is compared against a pandas.Series
            # If they are not series, then the program will crash
            else:
                prev_value1 = value1.shift(1)
                prev_value2 = value2.shift(1)
                return (prev_value1 <= prev_value2) & (value1 > value2)
        elif operator == "crosses-below":
            # In this case value2 must be a pandas Series
            # A constant crossing below a series is the same as the series crossing above the constant
            if type(value1) == float or type(value1) == int:
                prev_value2 = value2.shift(1)
                return (prev_value2 <= value1) & (value2 > value1)
            # In this case value1 must be a pandas Series
            elif type(value2) == float or type(value2) == int:
                prev_value1 = value1.shift(1)
                return (prev_value1 >= value2) & (prev_value1 < value2)
            # In this case a pandas.Series is compared against a pandas.Series
            # If they are not series, then the program will crash
            else:
                prev_value1 = value1.shift(1)
                prev_value2 = value2.shift(1)
                return (prev_value1 >= prev_value2) & (value1 < value2)
        else:
            raise NotImplementedError(f"Operator '{operator}' has not been implemented.")

    def evaluate_expression(self, expression : str) -> pd.Series:
        operator_stack = []
        operand_stack = []
        
        index = 0
        while index < len(expression):
            char = expression[index]
            # Skip blank spaces
            if char == " ":
                index += 1
                continue
            # It's a constant
            elif char.isdigit():
                start_idx = index
                # Get the constant substring
                while index < len(expression) and (char.isdigit() or char == "."):
                    index += 1
                    char = expression[index]
                # Push constant onto the operand stack
                operand_stack.append(float(expression[start_idx:index]))
                index -= 1
            elif char == "(":
                operator_stack.append("(")
            elif char == ")":
                # Calculate everything between parentheses
                while operator_stack[-1] != "(":
                    operand2 = operand_stack.pop()
                    operand1 = operand_stack.pop()
                    operator = operator_stack.pop()
                    result = Strategy.__apply_operator(operand1, operand2, operator)
                    operand_stack.push(result)
                operator_stack.pop()
            # It's a study
            elif char == "S" or char == "s":
                index += 1
                char = expression[index]
                start_idx = index
                # Get the study index
                while char.isdigit():
                    index += 1
                    if index == len(expression):
                        break
                    char = expression[index]
                study_idx = int(expression[start_idx:index])
                index -= 1
                study = self.studies_list[study_idx]
                study.calculate()
                # If the study requires a specific column (like bollinger bands lower, middle, or upper)
                if study_idx in self.desired_column:
                    # Push the study onto the operand stack
                    operand_stack.append(study.values[self.desired_column[study_idx]])
                else:
                    operand_stack.append(study.values)
            # It's an operator
            else:
                if char == "$":
                    start_idx = index + 1 # + 1 to ignore '$' symbol
                    # Find the closing '$' symbol
                    index = expression.find("$", start_idx)
                    operator = expression[start_idx:index]
                else:
                    start_idx = index
                    # Find the whole operator (should work for operators with more than one character)
                    while char.isdigit() is False and char.isalpha() is False:
                        index += 1
                        char = expression[index]
                    operator = expression[start_idx:index]
                    index -= 1
                while len(operator_stack) > 0 and Strategy.__precedence(operator) <= Strategy.__precedence(operator_stack[-1]):
                    result = Strategy.__apply_operator(operand1, operand2, operator)
                    operand_stack.append(result)
                operator_stack.append(operator)
            index += 1

        # All the characters in the expression have been visited and put on the stack
        # with some operations done whenever necessary.
        # Now just calculate everything you have in stack
        while len(operator_stack) > 0:
            operand2 = operand_stack.pop()
            operand1 = operand_stack.pop()
            operator = operator_stack.pop()
            result = Strategy.__apply_operator(operand1, operand2, operator)
            operand_stack.append(result)
        
        return operand_stack.pop()

    def generate_single_report(self) -> dict:
        # Main market data on which to trade
        main_market_data = self.market_data_list[0].candles
        current_symbol = self.main_symbols_list[self.current_main_symbol_index]
        opening_indices = []
        closing_indices = []
        opening_prices = []
        closing_prices = []
        lowest_pl = []
        highest_pl = []
        final_pl = []
        # Calculates statistics on all the trades resulting from a strategy:
        # %P/L
        # Min, max %P/L
        # Entry, exit price
        def trade_stats() -> pd.DataFrame:
            is_open = False
            for index in range(1, len(main_market_data.index)):
                # We look for an opening signal in previous index and open in the current one
                if self.opening_indices.iat[index - 1] and not is_open:
                    # Save the opening index, opening price
                    opening_indices.append(index)
                    opening_prices.append(main_market_data["open"].iat[index])
                    # Set the current highest and lowest prices for the trade
                    current_lowest = main_market_data["low"].iat[index]
                    current_highest = main_market_data["high"].iat[index]
                    is_open = True
                if self.closing_indices.iat[index - 1] and is_open:
                    # Save the closing index, closing price, lowest percent down, highest percent up, closing percent up/down
                    closing_indices.append(index)
                    closing_prices.append(main_market_data["open"].iat[index])
                    lowest_pl.append((current_lowest/opening_prices[-1] - 1) * 100)
                    highest_pl.append((current_highest/opening_prices[-1] - 1) * 100)
                    final_pl.append((closing_prices[-1]/opening_prices[-1] - 1) * 100)
                    is_open = False
                    # If the closing and opening condition occur simultaneously, then skip those indices (ignore them)
                    if opening_indices[-1] == closing_indices[-1]:
                        opening_indices.pop()
                        closing_indices.pop()
                if is_open:
                    # Update the current lowest and highest since open
                    current_lowest = min(current_lowest, main_market_data["low"].iat[index])
                    current_highest = max(current_highest, main_market_data["high"].iat[index])
            # If there is a trading signal without a closing signal then remove the last trade
            if len(opening_indices) > len(closing_indices):
                opening_indices.pop()
                opening_prices.pop()
            result = pd.DataFrame({ "symbol": current_symbol,
                                    "opening-date": main_market_data.index[opening_indices],
                                    "closing-date": main_market_data.index[closing_indices],
                                    "opening-price": opening_prices,
                                    "closing-price": closing_prices,
                                    "lowest-pl": lowest_pl,
                                    "highest-pl": highest_pl,
                                    "final-pl": final_pl})
            return result
        return trade_stats()
    
    def generate_global_report(self) -> None:
        prev_df = self.generate_single_report()
        for index in range(1, len(self.main_symbols_list)):
            self.current_main_symbol_index = index
            # Update the market data to the next one on the list
            self.market_data_list[0] = get_market_data(self.main_symbols_list[index],
                                      self.main_frequency_type,
                                      self.main_frequency,
                                      True)
            new_df = self.generate_single_report()
            prev_df = pd.concat([prev_df, new_df], ignore_index=True)
        prev_df.to_csv("report.csv", index=False)