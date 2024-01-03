from django.urls import path
from . import views

urlpatterns = [
    path('', views.base_view, name='base-view'),
    path('terms/', views.terms_view, name='terms-view'),
    path('contact-us/', views.contact_view, name='contact-view'),
    path('card/', views.cart_view, name='card-view'),
    path('ship/', views.ship_view, name='ship-view'),
    path('checkout/', views.checkout_view, name='checkout-view'),
    path('success/', views.success, name='success'),
    path('product/id', views.test_view, name='test-view'),
    path('collections/<str:category>', views.collections_by_category_view, name='collections_by_category'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('about/', views.about_view, name='about'),
    path('remove-from-cart/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
]
