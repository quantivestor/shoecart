from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import OuterRef, Subquery

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from ShoeCart.settings import EMAIL_HOST_USER

from .forms import CustomerRegistrationForm, FeedbackForm
from brand_module.models import Product, Brand
from .models import Cart, Customer, Feedback, Order

# Create your views here.
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get("size", None) 

    if not size:
        messages.error(request, "Please select a size before adding to cart.")
        return redirect('user_home') 
    
    # Create or update cart item
    cart_item, created = Cart.objects.get_or_create(
        user=request.user.customer,
        product=product,
        size=size,  # Save selected size
    )

    if not created:
        cart_item.quantity += 1  # If exists, increase quantity
        cart_item.save()

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

            # Create Order Entry
            order = Order.objects.create(
                user=request.user.customer,
                product=item.product,
                quantity=quantity,
                size=item.size,
                total_amount = item.product.discounted_price * quantity
            )

            # Remove item from cart
            item.delete()

            # Email content setup
            subject = f'Invoice for Your Order #{order.id}'
            context = {
                'order': order,
                'customer_name': order.user.user.username,
                'product_name': order.product.name,
                'price': order.product.discounted_price,
                'quantity': order.quantity,
                'total_price': order.product.discounted_price * order.quantity,
                'order_date': order.ordered_at,
            }

            # Load and render the email template
            html_message = render_to_string('brand/invoice_email.html', context)
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

        messages.success(request, "Order placed successfully!")
        return redirect('view_orders')

    return redirect('view_cart')

# View Orders
@login_required
def view_orders(request):
    feedback_subquery = Feedback.objects.filter(
        product=OuterRef('product'),
        customer=request.user.customer
    ).values('rating')[:1]

    # Annotate orders with feedback rating
    orders = Order.objects.filter(user=request.user.customer).select_related('product').annotate(
        feedback_rating=Subquery(feedback_subquery)
    )
    return render(request, 'customer/view_orders.html', {'orders': orders})

# Mark Order as Delivered (For Admin or Brand Use)
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

    # New Filters
    category = request.GET.get('category', '')
    color = request.GET.get('color', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    in_stock = request.GET.get('in_stock')

    products = Product.objects.all()
    categories = Product.objects.values_list('category', flat=True).distinct()
    colors = Product.objects.values_list('color', flat=True).distinct()

    # Filter by Product Name
    if product_name:
        products = products.filter(name__icontains=product_name)

    # Filter by Category
    if category:
        products = products.filter(category__iexact=category)

    # Filter by Color
    if color:
        products = products.filter(color__iexact=color)

    # Filter by Price Range
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Filter by In Stock
    if in_stock:
        products = products.filter(stock__gt=0)

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'customer/home.html', {'products': page_obj, 'categories': categories, 'colors': colors})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')

@login_required
def add_feedback(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.product = product
            feedback.customer = request.user.customer  # Assuming logged-in user is a customer
            feedback.save()
            messages.success(request, 'Your feedback has been submitted successfully.')
            return redirect('view_orders')  # Redirect to product details
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeedbackForm()

    return render(request, 'customer/add_feedback.html', {'form': form, 'product': product})