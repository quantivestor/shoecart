from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib import messages
from django.core.paginator import Paginator

from .forms import CustomerRegistrationForm
from shop_module.models import Product, Shop
from .models import Cart, Customer, Order

# Create your views here.
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart.objects.create(user=request.user.customer, product=product)
    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect('user_home')

# View Cart
@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user.customer).select_related('product')
    total_price = sum(item.product.price for item in cart_items)

    return render(request, 'customer/view_cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })

# Remove Product from Cart
@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user.customer)
    cart_item.delete()
    return redirect('view_cart')

@login_required
def place_order(request):
    if request.method == 'POST':
        selected_items = request.POST.getlist('selected_items')

        if not selected_items:
            messages.error(request, "Please select at least one item to proceed.")
            return redirect('view_cart')

        for item_id in selected_items:
            item = Cart.objects.get(id=item_id)
            quantity = int(request.POST.get(f'quantity_{item_id}'))

            # Check stock availability
            if item.product.stock < quantity:
                messages.error(request, f"Insufficient stock for {item.product.name}.")
                continue

            # Reduce stock and save order
            item.product.stock -= quantity
            item.product.save()

            # Create Order Entry
            Order.objects.create(
                user=request.user.customer,
                product=item.product,
                quantity=quantity,
            )

            # Remove item from cart
            item.delete()

        messages.success(request, "Order placed successfully!")
        return redirect('view_orders')

    return redirect('view_cart')

# View Orders
@login_required
def view_orders(request):
    orders = Order.objects.filter(user=request.user.customer).select_related('product')
    return render(request, 'customer/view_orders.html', {'orders': orders})

# Mark Order as Delivered (For Admin or Shop Use)
@login_required
def mark_order_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.is_delivered = True
    order.save()
    return redirect('view_orders')

def user_register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash password
            user.role = 'customer'  # Assuming you have a 'role' field in your User model
            user.save()
            
            # Create Customer Profile
            Customer.objects.create(user=user)

            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'customer/register.html', {'form': form})

@login_required
def user_home(request):
    product_name = request.GET.get('product_name', '')
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')

    # New Filters
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    in_stock = request.GET.get('in_stock')

    products = Product.objects.all()
    categories = Product.objects.values_list('category', flat=True).distinct()

    # Filter by Product Name
    if product_name:
        products = products.filter(name__icontains=product_name)

    # Filter by Category
    if category:
        products = products.filter(category__iexact=category)

    # Filter by Price Range
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Filter by In Stock
    if in_stock:
        products = products.filter(stock__gt=0)

    # Filter by Location (within 10km radius)
    if latitude and longitude:
        user_location = Point(float(longitude), float(latitude), srid=4326)
        shops = Shop.objects.annotate(distance=Distance('point', user_location)).filter(distance__lte=10000)
        products = products.filter(shop__in=shops)

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'customer/home.html', {'products': page_obj, 'categories': categories})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')