import  requests
import os

TELEGRAM = "5722155491:AAGUz30lSBkO5vn0cW8K8NNk5Lm6nnbFS9E" #TODO remove 

def send_telegram_message(message_text):
    url = f'https://api.telegram.org/bot{TELEGRAM}/sendMessage'
    params = {'chat_id': 329494298, 'text': message_text}
    response = requests.post(url, data=params)

def get_cart(request):
    """ Retrieve the cart from session """
    return request.session.get('cart', {})

def add_to_cart(request, product_id, quantity):
    """ Add a product to the cart or update its quantity """
    cart = get_cart(request)
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity
    request.session['cart'] = cart

def remove_from_cart(request, product_id):
    """ Remove a product from the cart """
    cart = get_cart(request)
    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart

def clear_cart(request):
    """ Clear the cart """
    request.session['cart'] = {}