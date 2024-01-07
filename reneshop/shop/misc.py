import  requests
from django.core.cache import cache
import os

TELEGRAM = "5722155491:AAGUz30lSBkO5vn0cW8K8NNk5Lm6nnbFS9E" #TODO remove 

def send_telegram_message(message_text):
    url = f'https://api.telegram.org/bot{TELEGRAM}/sendMessage'
    params = {'chat_id': 212283073, 'text': message_text}
    response = requests.post(url, data=params)


def get_conversion_rate(from_currency, to_currency):
    url = f"https://api.exchangeratesapi.io/latest?access_key=b97060ed91b1b945b641a884f02e5d35&base={from_currency}"
    response = requests.get(url)
    data = response.json()
    return data['rates'][to_currency]


def get_conversion_rate(from_currency, to_currency):
    # Check if rate is in cache
    rate = cache.get(f'{from_currency}_to_{to_currency}')
    if not rate:
        # If not in cache, fetch from API and cache it
        rate = get_conversion_rate(from_currency, to_currency)
        if rate:
            cache.set(f'{from_currency}_to_{to_currency}', rate, timeout=86400)  # Cache for 1 hour
    return rate