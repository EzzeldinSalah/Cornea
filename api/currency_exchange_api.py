import requests
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

CURRENCY_EXCHANGE_API_URL = os.getenv("CURRENCY_EXCHANGE_API_URL")

# LOL I don't know how it works 😂🥀✌🏻
def currency_exchange_converter(x: str, y: str):
    res = requests.get(CURRENCY_EXCHANGE_API_URL)
    return res.json()[x][y]

if __name__ == "__main__":
    print(currency_exchange_converter('usd', 'egp'))