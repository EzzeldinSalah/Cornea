import requests
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

CURRENCY_EXCHANGE_API_URL = os.getenv("CURRENCY_EXCHANGE_API_URL")

def currency_exchange_converter(base_currency: str, target_currency: str) -> float:
    response = requests.get(CURRENCY_EXCHANGE_API_URL)
    return response.json()[base_currency][target_currency]

if __name__ == "__main__":
    print(currency_exchange_converter('usd', 'egp'))