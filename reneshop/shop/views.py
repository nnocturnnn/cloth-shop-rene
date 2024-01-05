from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Customer, ProductImage
from .misc import send_telegram_message
from django.views.decorators.http import require_POST
import os 
from cloudipsp import Api, Checkout
from decimal import Decimal

api = Api(merchant_id=1539357,
          secret_key=os.environ.get("FONDY_SK"))

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
    context.update({'currency_code': request.GET.get('cur', 'EUR')})
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
                'total_price': total_price * rate[0]
            }
        except Product.DoesNotExist:
            print(f"Product with id {product_id} does not exist.")

    total_items = sum(item['quantity'] for item in detailed_cart.values())
    total_price = sum(item['total_price'] for item in detailed_cart.values())
    checkout = Checkout(api=api)
    data = {
        "currency": currency_code,
        "amount": str(int(total_price) * 100)
    }
    url = checkout.url(data).get('checkout_url')
    

    context = {
        'cart': detailed_cart,
        'total_items': total_items,
        'total_price': total_price,
        'currency_char': rate[1],
        'url_pay' : url,
    }

    return render_with_categories(request, 'card.html', context)

def checkout_view(request):
    return render_with_categories(request, 'checkout.html')

def success(request):
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
    product = get_object_or_404(Product, pk=product_id)
    images = ProductImage.objects.filter(product=product)
    context = {'product': product, 'images': images}
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