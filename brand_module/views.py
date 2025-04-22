from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from admin_module.models import User
from customer_module.models import Feedback, Order
from ShoeCart.settings import EMAIL_HOST_USER

from .forms import (ProductForm, brandLoginForm, brandProfileForm,
                    brandRegistrationForm)
from .models import Brand, Product


# Create your views here.
@login_required(login_url="login")
def brand_home(request):
    return render(request, "brand/brand_dashboard.html")


@login_required(login_url="login")
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.brand = request.user.brand
            product.save()
            return redirect("view_products")
    else:
        form = ProductForm()
    return render(request, "brand/add_product.html", {"form": form})


@login_required(login_url="login")
def view_products(request):
    products = Product.objects.filter(brand=request.user.brand)
    return render(request, "brand/view_products.html", {"products": products})


@login_required(login_url="login")
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("view_products")
    else:
        form = ProductForm(instance=product)
    return render(
        request, "brand/update_product.html", {"form": form, "product": product}
    )


@login_required(login_url="login")
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        product.delete()
        return redirect("view_products")
    return render(request, "brand/delete_product.html", {"product": product})


@login_required(login_url="login")
def view_feedbacks(request):
    # Filter feedbacks for products belonging to the requested brand
    feedbacks = Feedback.objects.filter(
        order__product__brand=request.user.brand
    ).select_related("order", "customer")

    return render(
        request,
        "brand/view_feedbacks.html",
        {
            "feedbacks": feedbacks,
        },
    )


@login_required(login_url="login")
def view_sell_history(request):
    # Get the brand owned by the logged-in user
    brand = Brand.objects.get(user=request.user)

    # Filter orders for items belonging to the logged-in user's brand
    sell_history = Order.objects.filter(product__brand=brand).select_related(
        "product", "user"
    ).order_by("-ordered_at")

    return render(
        request,
        "brand/view_sell_history.html",
        {
            "sell_history": sell_history,
        },
    )


def brand_register(request):
    if request.method == "POST":
        form = brandRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    email=form.cleaned_data["email"],  # Add email here
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"],
                    role="brand",  # Assuming role management is in place
                )
                Brand.objects.create(
                    user=user,
                    brand_name=form.cleaned_data["brand_name"],
                    address=form.cleaned_data["address"],
                    # point=point,
                    contact_info=form.cleaned_data["contact_info"],
                )
                messages.success(request, "Brand registered successfully! Please log in.")
                return redirect("login")
            except Exception as e:
                messages.error(request, "Email already taken")
    else:
        form = brandRegistrationForm()
    return render(request, "brand/brand_register.html", {"form": form})


def brand_login(request):
    if request.method == "POST":
        form = brandLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None and hasattr(user, "brand"):
                login(request, user)
                messages.success(request, "Login successful!")
                return redirect("brand_dashboard")  # Redirect to brand dashboard
            else:
                messages.error(request, "Invalid credentials or account not approved.")
    else:
        form = brandLoginForm()
    return render(request, "brand/brand_login.html", {"form": form})


# Brand Logout View
@login_required(login_url="login")
def brand_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")


@login_required(login_url="login")
def brand_profile(request):
    brand = request.user.brand  # Access the brand linked to the logged-in user

    if request.method == "POST":
        form = brandProfileForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            return redirect("brand_dashboard")
    else:
        form = brandProfileForm(instance=brand)

    return render(request, "brand/profile.html", {"form": form})


@login_required(login_url="login")
def approve_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Mark the order as delivered
    order.is_delivered = True
    order.save()

    # Email content setup
    subject = f"Invoice for Your Order #{order.id}"
    context = {
        "order": order,
        "customer_name": order.user.user.username,
        "product_name": order.product.name,
        "price": order.product.price,
        "quantity": order.quantity,
        "total_price": order.product.price * order.quantity,
        "order_date": order.ordered_at,
    }

    # Load and render the email template
    html_message = render_to_string("brand/invoice_email.html", context)
    plain_message = strip_tags(
        html_message
    )  # Fallback for clients that don't support HTML
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
        messages.success(request, "Order approved and invoice sent successfully!")
    except Exception as e:
        messages.error(request, f"Order approved, but email failed: {e}")

    return redirect("view_sell_history")


@login_required(login_url="login")
def reject_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect("view_sell_history")
