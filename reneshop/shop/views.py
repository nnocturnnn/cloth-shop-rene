from django.shortcuts import render, get_object_or_404
from .models import Category, Product, Customer, ProductImage
from .misc import send_telegram_message, add_to_cart, get_cart, remove_from_cart, clear_cart
# import stripe
from django.views.decorators.http import require_POST
import os 

# stripe.api_key = os.getenv("STRIPE_API")

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

    return render(request, template_name, context)

def contact_view(request):
    return render_with_categories(request, 'contact.html')

def terms_view(request):
    return render_with_categories(request, 'term.html')

def ship_view(request):
    return render_with_categories(request, 'ship.html')

def card_view(request):
    return render_with_categories(request, 'card.html')

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
    product = get_object_or_404(Product, pk=product_id)

    # Initialize the cart in the session if it doesn't exist
    if 'cart' not in request.session or not request.session['cart']:
        request.session['cart'] = {}

    # Add or update the product in the cart
    cart = request.session['cart']
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {'quantity': quantity, 'price': str(product.price)}