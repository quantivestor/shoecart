from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.contrib.auth.decorators import login_required

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from admin_module.models import User
from customer_module.models import Feedback, Order
from ecommerce.settings import EMAIL_HOST_USER
from .forms import ProductForm, ShopLoginForm, ShopProfileForm, ShopRegistrationForm
from .models import Product, Shop

# Create your views here.
@login_required
def shop_home(request):
    return render(request, 'shop/shop_dashboard.html')

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES) 
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = request.user.shop
            product.save()
            return redirect('view_products')
    else:
        form = ProductForm()
    return render(request, 'shop/add_product.html', {'form': form})

@login_required
def view_products(request):
    products = Product.objects.filter(shop=request.user.shop)
    return render(request, 'shop/view_products.html', {'products': products})

@login_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product) 
        if form.is_valid():
            form.save()
            return redirect('view_products')
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop/update_product.html', {'form': form, 'product': product})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('view_products')
    return render(request, 'shop/delete_product.html', {'product': product})

@login_required
def view_feedbacks(request):
    # Filter feedbacks for products belonging to the requested shop
    feedbacks = Feedback.objects.filter(product__shop=request.user.shop).select_related('product', 'customer')
    
    return render(request, 'shop/view_feedbacks.html', {
        'feedbacks': feedbacks,
    })

@login_required
def view_sell_history(request):
    # Get the shop owned by the logged-in user
    shop = Shop.objects.get(user=request.user)
    
    # Filter orders for items belonging to the logged-in user's shop
    sell_history = Order.objects.filter(product__shop=shop).select_related('product', 'user')
    
    return render(request, 'shop/view_sell_history.html', {
        'sell_history': sell_history,
    })

def shop_register(request):
    if request.method == 'POST':
        form = ShopRegistrationForm(request.POST)
        if form.is_valid():
            point_data = form.cleaned_data['point'].split(",")
            latitude = float(point_data[0].strip())
            longitude = float(point_data[1].strip())
            point = Point(longitude, latitude, srid=4326)

            user = User.objects.create_user(
                email=form.cleaned_data['email'],       # Add email here
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                role='shop'  # Assuming role management is in place
            )
            Shop.objects.create(
                user=user,
                shop_name=form.cleaned_data['shop_name'],
                address=form.cleaned_data['address'],
                point=point,
                contact_info=form.cleaned_data['contact_info']
            )
            messages.success(request, 'Shop registered successfully! Please log in.')
            return redirect('login')
    else:
        form = ShopRegistrationForm()
    return render(request, 'shop/shop_register.html', {'form': form})


def shop_login(request):
    if request.method == 'POST':
        form = ShopLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None and hasattr(user, 'shop'):
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('shop_dashboard')  # Redirect to shop dashboard
            else:
                messages.error(request, 'Invalid credentials or account not approved.')
    else:
        form = ShopLoginForm()
    return render(request, 'shop/shop_login.html', {'form': form})

# Shop Logout View
def shop_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')

@login_required
def shop_profile(request):
    shop = request.user.shop  # Access the shop linked to the logged-in user

    if request.method == 'POST':
        form = ShopProfileForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            return redirect('shop_dashboard')
    else:
        form = ShopProfileForm(instance=shop)

    return render(request, 'shop/profile.html', {'form': form})

@login_required
def approve_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Mark the order as delivered
    order.is_delivered = True
    order.save()

    # Email content setup
    subject = f'Invoice for Your Order #{order.id}'
    context = {
        'order': order,
        'customer_name': order.user.user.username,
        'product_name': order.product.name,
        'price': order.product.price,
        'quantity': order.quantity,
        'total_price': order.product.price * order.quantity,
        'order_date': order.ordered_at,
    }

    # Load and render the email template
    html_message = render_to_string('shop/invoice_email.html', context)
    plain_message = strip_tags(html_message)  # Fallback for clients that don't support HTML
    recipient_email = order.user.user.email

    # Send email
    try:
        send_mail(
            subject,
            plain_message,
            EMAIL_HOST_USER,  # Sender's email
            [recipient_email],
            html_message=html_message,
        )
        messages.success(request, 'Order approved and invoice sent successfully!')
    except Exception as e:
        messages.error(request, f'Order approved, but email failed: {e}')

    return redirect('view_sell_history')


@login_required
def reject_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    item = Product.objects.get(id=order.product.id)
    item.stock += order.quantity
    item.save()
    return redirect('view_sell_history')