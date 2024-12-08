from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Cart, Product, CartItem, UserProfile
from decimal import Decimal  

# Home page view
def home(request):
    return render(request, 'home.html')

# User registration
def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# User login
def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('user_home')
    return render(request, 'login.html', {'form': form})

# View categories
def categories(request):
    unique_categories = Product.objects.values('category').distinct()
    return render(request, 'categories.html', {'categories': unique_categories})

@login_required
def set_budget(request):
    if request.method == 'POST':
        budget = request.POST.get('budget')
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        user_profile.budget = budget
        user_profile.save()
    return redirect('user_home')

# View products by category
def view_products_by_category(request, category):
    products = Product.objects.filter(category=category)
    data = {'category': category, 'products': products}
    return render(request, 'products_by_category.html', data)

# View cart
@login_required
def view_cart(request):
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = user_cart.cartitem_set.all()

    cart_items_data = [
        {
            'product_name': item.product.name,
            'quantity': item.quantity,
            'total_price': item.product.price * item.quantity,
            'id': item.product.id,
            'category': item.product.category
        }
        for item in cart_items
    ]
    total_price = sum(item['total_price'] for item in cart_items_data)
    context = {'cart_items_data': cart_items_data, 'total_price': total_price}
    return render(request, 'cart.html', context)

# Add to cart
@login_required
def add_to_cart(request, product_id):
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    product = Product.objects.get(pk=product_id)
    category = product.category

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart_item, created = CartItem.objects.get_or_create(cart=user_cart, product=product)
        cart_item.quantity = quantity
        cart_item.save()
        return redirect('products_by_category', category=category)

# Remove from cart
@login_required
def remove_from_cart(request, product_id, quantity):
    try:
        user_cart = Cart.objects.get(user=request.user)
        product = Product.objects.get(pk=product_id)
        cart_item = CartItem.objects.get(cart=user_cart, product=product)
        if cart_item.quantity > quantity:
            cart_item.quantity -= quantity
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        return HttpResponseBadRequest("The item is not in the cart.")
    return redirect('view_cart')


# Checkout
@login_required
def checkout(request):
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = user_cart.cartitem_set.all()

    quantity_discount_threshold = 4
    if len(cart_items) > quantity_discount_threshold:
        discount_percentage = 15
    else:
        discount_percentage = 0

    coupon_code = request.GET.get('coupon_code')
    total_price = 0
    cart_items_with_totals = [] 
    for item in cart_items:
        item_price = item.product.price * item.quantity
        if coupon_code and coupon_code.lower() in ['discount', 'abcd', 'xyz']:
            item_price *= Decimal('0.8')  # Apply 20% discount
        # Convert discount_percentage to Decimal before division
        total_price += item_price * (Decimal(1) - Decimal(discount_percentage) / Decimal(100))
        cart_items_with_totals.append({
            "product": item.product,
            "quantity": item.quantity,
            "total_price": item_price  # Total for this item
        })
    user_budget = request.user.userprofile.budget
    if total_price > user_budget:
        messages.warning(request, f"Warning: Total price ({total_price}) exceeds budget ({user_budget}).")

    data = {'cart_items': cart_items_with_totals, 'total_price': total_price}
    return render(request, 'checkout.html', data)

# Process payment
@login_required
def process_payment(request):
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    payment_method = request.POST.get('payment_method')
    total_price = request.POST.get('total_price')

    if payment_method == 'credit card':
        payment_result = f'Paid ${total_price} using Credit Card'
    elif payment_method == 'paypal':
        payment_result = f'Paid ${total_price} using PayPal'
    else:
        return render(request, 'checkout.html', {'error_message': 'Invalid payment method'})

    user_cart.cartitem_set.all().delete()
    return render(request, 'order_placed.html', {'data': payment_result})
