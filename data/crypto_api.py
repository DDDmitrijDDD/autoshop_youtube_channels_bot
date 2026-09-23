import requests
import json
from data.config import API_KEY, SHOP_ID


async def create_check(amount):
    url = "https://api.trybit.com/v2/invoice/create"
    headers = {
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "amount": amount,
        "shop_id": SHOP_ID,
        "currency": "USD",
        "add_fields": {"time_to_pay": {
        "hours": 0, "minutes": 30
    }}
    }


    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
         return response.json()
    else:
        return response.status_code, response.text


async def check_check(ids):
    url = "https://api.trybit.com/v2/invoice/merchant/info"
    headers = {
        "Authorization": f"Token {API_KEY}"
    }
    data = {
        "uuids": [f"{ids}"]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code, response.text


async def delete_check(ids):
    url = "https://api.trybit.com/v2/invoice/merchant/canceled"
    headers = {
        "Authorization": f"Token {API_KEY}"
    }
    data = {
        "uuid": f"{ids}"}

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code, response.text