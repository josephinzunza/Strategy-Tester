import base64
from datamodels import MarketData
from enums import PeriodType, FrequencyType
import json 
import requests
import time
import webbrowser

class SchwabAPIClient:
    def __init__(self) -> None:
        self.key, self.secret = self.__load_credentials()
        self.start_time = 0
        self.end_time = 0
        tokens_dict = self.__load_tokens()
        try:
            self.refresh_token = tokens_dict["refresh_token"]
            self.access_token = tokens_dict["access_token"]
            expiration = tokens_dict["expiration"]
            seconds_until_exp = expiration - time.time()
            # Tokens found already expired
            if (seconds_until_exp <= 0):
                self.first_time_setup()
            # Tokens found will expire within 5 minutes
            elif (seconds_until_exp <= 300):
                self.refresh_tokens()
        except KeyError:
            self.first_time_setup()
         
    def __load_credentials(self) -> tuple[str, str]:
        with open("credentials.json") as file:
            data = json.load(file)
        return (data["key"], data["secret"])

    def __construct_init_auth_url(self) -> tuple[str, str, str]:
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={self.key}&redirect_uri=https://127.0.0.1"

        print("Click to authenticate:")
        print(auth_url)

        return auth_url
    
    def __load_tokens(self) -> dict:
        try:
            with open("tokens.json") as file:
                return json.load(file) 
        except:
            print("No tokens were found")
            return {}

    def __construct_headers_and_payload(self, returned_url):
        response_code = f"{returned_url[returned_url.index('code=') + 5: returned_url.index('%40')]}@"

        credentials = f"{self.key}:{self.secret}"
        base64_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {base64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        payload = {
            "grant_type": "authorization_code",
            "code": response_code,
            "redirect_uri": "https://127.0.0.1",
        }

        return headers, payload


    def __retrieve_tokens(self, headers, payload) -> dict:
        init_token_response = requests.post(
            url="https://api.schwabapi.com/v1/oauth/token",
            headers=headers,
            data=payload,
        )

        init_tokens_dict = init_token_response.json()

        return init_tokens_dict
        
    def refresh_tokens(self) -> None:
        print("Initializing...")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        headers = {
            "Authorization": f'Basic {base64.b64encode(f"{self.key}:{self.secret}".encode()).decode()}',
            "Content-Type": "application/x-www-form-urlencoded",
        }

        refresh_token_response = requests.post(
            url="https://api.schwabapi.com/v1/oauth/token",
            headers=headers,
            data=payload,
        )
        if refresh_token_response.status_code == 200:
            print("Retrieved new tokens successfully using refresh token.")
        else:
            print(f"Error refreshing access token: {refresh_token_response.text}")
            return None

        refresh_token_dict = refresh_token_response.json()

        custom_dict = {}
        custom_dict["refresh_token"] = refresh_token_dict["refresh_token"]
        custom_dict["access_token"] = refresh_token_dict["access_token"]
        custom_dict["id_token"] = refresh_token_dict["id_token"]
        custom_dict["expiration"] = self.start_time + 1800

        with open("tokens.json", "w", encoding="utf-8") as file:
            json.dump(custom_dict, file, ensure_ascii=False, indent=4)
        
        print("Tokens refreshed successfully")

    def first_time_setup(self) -> None:
        cs_auth_url = self.__construct_init_auth_url()
        webbrowser.open(cs_auth_url)

        print("Paste Returned URL:")
        returned_url = input()

        init_token_headers, init_token_payload = self.__construct_headers_and_payload(returned_url)

        init_tokens_dict = self.__retrieve_tokens(headers=init_token_headers, payload=init_token_payload)
        self.start_time = time.time()
        self.end_time = self.start_time + 1500 # Expiration will be in 25 minutes (1500 seconds)

        custom_dict = {}
        custom_dict["refresh_token"] = init_tokens_dict["refresh_token"]
        custom_dict["access_token"] = init_tokens_dict["access_token"]
        custom_dict["id_token"] = init_tokens_dict["id_token"]
        custom_dict["expiration"] = self.start_time + 1800

        with open("tokens.json", "w", encoding="utf-8") as file:
            json.dump(custom_dict, file, ensure_ascii=False, indent=4)
        
        print("Tokens obtained successfully")

    def get_price_history(self, symbol : str,
                        period_type : PeriodType,
                        period : int,
                        frequency_type : FrequencyType,
                        frequency : int,
                        start_date : int = None,
                        end_date : int = None,
                        need_extended_hours_data : bool = None,
                        need_previous_close : bool = None) -> MarketData:
        
        endpoint = "https://api.schwabapi.com/marketdata/v1/pricehistory"

        payload = {
                "symbol": symbol,
                "periodType": period_type.name.lower(),
                "period": period,
                "frequencyType": frequency_type.name.lower(),
                "frequency": frequency
            }
        if (start_date != None):
            payload["startDate"] = start_date
        if (end_date != None):
            payload["endDate"] = end_date
        if (need_extended_hours_data != None):
            payload["needExtendedHoursData"] = need_extended_hours_data
        if (need_previous_close != None):
            payload["needPreviousClose"] = need_previous_close
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        price_history_response = requests.get(
                url=endpoint,
                headers=headers,
                params=payload,
            )
        
        if price_history_response.status_code != 200:
            print(f"Error obtaining price history: {price_history_response.text}")
            return None
        
        price_history_dict = price_history_response.json()

        price_history = MarketData(
            symbol,
            price_history_dict["candles"],
            frequency_type,
            frequency
        )

        return price_history