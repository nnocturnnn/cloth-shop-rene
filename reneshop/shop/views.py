from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Customer, ProductImage
from .misc import send_telegram_message
from django.views.decorators.http import require_POST
import os 
import stripe
from django.conf import settings
from decimal import Decimal

stripe.api_key = os.getenv('STRIPE_API')

shipping_rate = stripe.ShippingRate.create(
    display_name='Standard shipping',
    type='fixed_amount',
    fixed_amount={
        'amount': 1000,  # This is in the smallest currency unit, e.g., cents for USD
        'currency': 'usd',
    },
    delivery_estimate={
        'minimum': {
            'unit': 'business_day',
            'value': 5,
        },
        'maximum': {
            'unit': 'business_day',
            'value': 15,
        },
    }
)

def base_view(request):
    return render_with_categories(request, 'index.html')

def get_categories():
    return Category.objects.all()

def render_with_categories(request, template_name, context={}):
    categories = get_categories()

    if request.method == 'POST':
        if 'email_form' in request.POST:
            email = request.POST.get('email')
            if email:
                existing_customer = Customer.objects.filter(email=email).first()
                if not existing_customer:
                    new_customer = Customer(email=email)
                    new_customer.save()
            success_message = "Thank you for subscribe to NEWSLETTER"
        elif 'ship_form' in request.POST:
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            email = request.POST.get('email')
            order_id = request.POST.get('order_id')
            message = request.POST.get('message')
            send_telegram_message(f"New Form Submission:\nName: {name}\nPhone: {phone}\nEmail: {email}\nOrder ID: {order_id}\nMessage: {message}")
            success_message = "Thank you for contact us"
        elif 'contact_form' in request.POST:
            name = request.POST.get('name')
            email = request.POST.get('email')
            message = request.POST.get('message')
            send_telegram_message(f"New Form Submission:\nName: {name}\nEmail: {email}\nMessage: {message}")
            success_message = "Thank you for contact us"

        return render(request, 'success.html', {'success_message': success_message})  # Replace 'success.html' with your success template
    context.update({'categories': categories})
    context.update({'currency_code': request.GET.get('cur', 'USD')})
    context.update({'lencart': len(request.session.get('cart', {}))})

    return render(request, template_name, context)

def contact_view(request):
    return render_with_categories(request, 'contact.html')

def terms_view(request):
    return render_with_categories(request, 'term.html')

def ship_view(request):
    return render_with_categories(request, 'ship.html')


def about_view(request):
    return render_with_categories(request, 'about.html')

def cart_view(request):
    cart = request.session.get('cart', {})
    detailed_cart = {}
    currency_code = request.GET.get('cur', 'USD').upper()
    conversion_rates = {
        'USD': (Decimal(1), '$'),
        'EUR': (Decimal(0.91), '€'),
        'ILS': (Decimal(3.69), '₪'),
        'UAH': (Decimal(38.09), '₴'),
    }
    rate = conversion_rates.get(currency_code, (1, '$'))
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            total_price = product.price * item['quantity']
            detailed_cart[product_id] = {
                'product_name': product.name,
                'price': product.price * rate[0],
                'quantity': item['quantity'],
                'total_price': total_price * rate[0],
                'description' : product.description,
            }
        except Product.DoesNotExist:
            print(f"Product with id {product_id} does not exist.")

    total_items = sum(item['quantity'] for item in detailed_cart.values())
    total_price = sum(item['total_price'] for item in detailed_cart.values())
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': currency_code.lower(),
                        'unit_amount': int(total_price) * 100,
                        'product_data': {
                            'name': detailed_cart['1']['product_name'],
                            'description' : detailed_cart['1']['description'].replace("<br>","\n"),
                            'images' : ['https://storage.googleapis.com/rene-shop/1.jpg'],
                        },
                    },
                    'quantity': 1,
                },
            ],
            shipping_address_collection={
                'allowed_countries': getattr(settings, 'ALL_COUNTRY_CODES', ''),
            },
            shipping_options=[
                {
                    'shipping_rate': shipping_rate.id,
                },
            ],
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),  # Adjust with your success route
            cancel_url=request.build_absolute_uri('/card'),  # Adjust with your cancel route
        )

        payment_url = checkout_session.url

    except Exception as e:
        print(f"An error occurred: {e}")
        payment_url = None

    context = {
        'cart': detailed_cart,
        'total_items': total_items,
        'total_price': total_price,
        'currency_char': rate[1],
        'url_pay' : payment_url,
    }

    return render_with_categories(request, 'card.html', context)

def checkout_view(request):
    return render_with_categories(request, 'checkout.html')

def success(request):
    cart = request.session.get('cart', {})
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            product.quantity -= item['quantity']
            product.save()
        except:
            print(f"Product with id {product_id} does not exist.")
    
    request.session['cart'] = {}
    request.session.modified = True
    send_telegram_message("New Order is placed")

    return render_with_categories(request, 'success.html')

def test_view(request):
    return render(request, 'productpage.html')

def collections_by_category_view(request, category):
    if category == "all":
        items = Product.objects.all()
        items_list = list(items.values())
        context = {
            "products" : items_list,
            "category" : None,
        }
    else:
        items = Product.objects.filter(category__name__iexact=category)
        items_list = list(items.values())
        context = {
            "products" : items_list,
            "category" : Category.objects.get(name=category),
        }


    return render_with_categories(request, "category.html" ,context)


def product_detail(request, product_id):
    currency_code = request.GET.get('cur', 'USD').upper()
    product = get_object_or_404(Product, pk=product_id)
    conversion_rates = {
        'USD': (Decimal(1), '$'),
        'EUR': (Decimal(0.91), '€'),
        'ILS': (Decimal(3.69), '₪'),
        'UAH': (Decimal(38.09), '₴'),
    }
    rate = conversion_rates.get(currency_code, (1, '$'))
    product.updated_price *= rate[0] 
    images = ProductImage.objects.filter(product=product)
    context = {'product': product, 'images': images, 'currency_char': rate[1]}
    return render_with_categories(request, 'productpage.html', context)

@require_POST
def add_to_cart(request):
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))

    # Initialize the cart in the session if it doesn't exist
    if 'cart' not in request.session or not request.session['cart']:
        request.session['cart'] = {}

    # Add or update the product in the cart
    cart = request.session['cart']
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {'quantity': quantity}

    request.session.modified = True
    return  redirect(request.META.get('HTTP_REFERER', '/'))


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if product_id in cart:
        del cart[product_id]  # Remove the item from the cart

    request.session['cart'] = cart  # Update the session cart
    request.session.modified = True  # Mark the session as "modified" to make sure it gets saved

    return redirect('/card') 


@require_POST
def update_cart(request):
    product_id = request.POST.get('product_id')
    new_quantity = int(request.POST.get('new_quantity', 1))

    # Logic to update the cart in the session
    if 'cart' in request.session and product_id in request.session['cart']:
        if new_quantity > 0:
            request.session['cart'][product_id]['quantity'] = new_quantity
        else:
            # Consider removing the item if the quantity is set to 0 or less
            del request.session['cart'][product_id]
            
    request.session.modified = True
    return redirect("/card")