from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Avg, Count

from brand_module.models import Product
from ShoeCart.settings import EMAIL_HOST_USER

from .forms import CustomerRegistrationForm, FeedbackForm
from .models import Cart, Customer, Feedback, Order, Transaction


@login_required(login_url="login")
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get("size", None)

    if not size:
        messages.error(request, "Please select a size before adding to cart.")
        return redirect("product_list")

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
    return redirect("product_list")


# View Cart
@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user.customer).select_related(
        "product"
    )
    total_price = sum(item.product.discounted_price for item in cart_items)

    return render(
        request,
        "customer/view_cart.html",
        {"cart_items": cart_items, "total_price": total_price},
    )


# Remove Product from Cart
@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user.customer)
    cart_item.delete()
    return redirect("view_cart")


@login_required
def confirm_order(request):
    if request.method == "POST":
        selected_items = request.POST.getlist("selected_items")

        if not selected_items:
            messages.error(request, "Please select items to proceed.")
            return redirect("view_cart")

        selected_products = []
        total_amount = 0

        for item_id in selected_items:
            item = Cart.objects.get(id=item_id)
            quantity = int(request.POST.get(f"quantity_{item_id}", 1))
            total_price = item.product.discounted_price * quantity
            total_amount += total_price

            selected_products.append(
                {
                    "id": item.id,
                    "product": item.product,
                    "quantity": quantity,
                    "total_price": total_price,
                }
            )

        return render(
            request,
            "customer/confirm_order.html",
            {
                "selected_items": selected_products,
                "total_amount": total_amount,
            },
        )

    return redirect("view_cart")


@login_required
def place_order(request):
    if request.method == "POST":
        selected_items = request.POST.getlist("selected_items")
        delivery_address = request.POST.get("address")
        card_number = request.POST.get("card_number")
        card_expiry = request.POST.get("expiry_date")
        card_cvv = request.POST.get("cvv")

        if not selected_items:
            messages.error(request, "Please select at least one item to proceed.")
            return redirect("view_cart")

        # with transaction.atomic():
        for item_id in selected_items:
            item = Cart.objects.get(id=item_id)
            quantity = int(request.POST.get(f"quantity_{item_id}", 1))

            # Stock Check
            if item.product.stock < quantity:
                messages.error(
                    request, f"Insufficient stock for {item.product.name}."
                )
                continue

            # Reduce stock
            item.product.stock -= quantity
            item.product.save()

            # Create Order Entry
            order = Order.objects.create(
                user=request.user.customer,
                product=item.product,
                quantity=quantity,
                size=item.size,
                total_amount=item.product.discounted_price * quantity,
                delivery_address=delivery_address,
            )

            # Save Advance Payment Transaction
            Transaction.objects.create(
                order=order,
                payment_id=f"ADV-{order.id}",
                amount=item.product.discounted_price * quantity,
                status="Completed",
                card_number=card_number,
                card_expiry=card_expiry,
                card_cvv=card_cvv,
            )

            # Remove item from cart
            item.delete()

            # Email content setup
            subject = f"Invoice for Your Order #{order.id}"
            context = {
                "order": order,
                "customer_name": order.user.user.username,
                "product_name": order.product.name,
                "price": order.product.discounted_price,
                "quantity": order.quantity,
                "total_price": order.product.discounted_price * order.quantity,
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
                messages.success(
                    request, "Order approved and invoice sent successfully!"
                )
            except Exception as e:
                messages.error(request, f"Order approved, but email failed: {e}")

        messages.success(request, "Order placed successfully!")
        return redirect("view_orders")

    return redirect("view_cart")

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user.customer)

    # if order.status == "Delivered":
    #     messages.error(request, "You cannot cancel a delivered order.")
    #     return redirect("view_orders")

    # Restock product
    order.product.stock += order.quantity
    order.product.save()

    # Update order status to 'Cancelled'
    order.status = "Cancelled"
    order.track_status = "Cancelled"
    order.save()

    transaction = Transaction.objects.get(order=order)
    transaction.status = "Refunded"
    transaction.save()

    send_mail(
        "Order Cancelled & Refund Issued",
        f"Dear {order.user.user.username},\n\n"
        f"Your order for {order.product.name} has been cancelled.\n"
        f"A refund of ₹{order.total_amount} has been processed.\n\n"
        "Thank you for shopping with us!",
        EMAIL_HOST_USER,
        [order.user.user.email],
        fail_silently=False,
    )

    messages.success(
        request,
        f"Order cancelled. ₹{order.total_amount:.2f} has been refunded.",
    )
    return redirect("view_orders")


# View Orders
@login_required
def view_orders(request):
    feedback_subquery = Feedback.objects.filter(
        product=OuterRef("product"), customer=request.user.customer
    ).values("rating")[:1]

    # Annotate orders with feedback rating
    orders = (
        Order.objects.filter(user=request.user.customer)
        .select_related("product")
        .annotate(feedback_rating=Subquery(feedback_subquery))
        .order_by("-ordered_at")
    )

    return render(request, "customer/view_orders.html", {"orders": orders})


# Mark Order as Delivered (For Admin or Brand Use)
@login_required
def mark_order_delivered(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.is_delivered = True
    order.save()
    return redirect("view_orders")


def user_register(request):
    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])  # Hash password
            user.role = (
                "customer"  # Assuming you have a 'role' field in your User model
            )
            user.save()

            # Create Customer Profile
            Customer.objects.create(
                user=user,
                phone_number=form.cleaned_data["phone_number"],
                left_image=form.cleaned_data["left_image"],  # Correct way to retrieve image
                straight_image=form.cleaned_data["straight_image"],
                right_image=form.cleaned_data["right_image"],
            )

            messages.success(request, "Registration successful. Please log in.")
            return redirect("login")
    else:
        form = CustomerRegistrationForm()

    return render(request, "customer/register.html", {"form": form})


def user_home(request):
    product_name = request.GET.get("product_name", "").strip()
    category = request.GET.get("category", "").strip()
    color = request.GET.get("color", "").strip()
    material = request.GET.get("material", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    in_stock = request.GET.get("in_stock")
    brand_name = request.GET.get("brand_name", "").strip()

    products = Product.objects.all()

    # Fetch distinct values for filtering
    categories = Product.objects.values_list("category", flat=True).distinct()
    colors = Product.objects.values_list("color", flat=True).distinct()
    materials = Product.objects.values_list("material", flat=True).distinct()
    brands = Product.objects.values_list("brand__brand_name", flat=True).distinct()  # Corrected

    # Apply Filters
    if product_name:
        products = products.filter(name__icontains=product_name)

    if category:
        products = products.filter(category__iexact=category)

    if material:
        products = products.filter(material__iexact=material)

    if color:
        products = products.filter(color__iexact=color)

    if min_price:
        try:
            min_price = float(min_price)
            products = products.filter(price__gte=min_price)
        except ValueError:
            pass  # Ignore invalid price values

    if max_price:
        try:
            max_price = float(max_price)
            products = products.filter(price__lte=max_price)
        except ValueError:
            pass

    if in_stock:
        products = products.filter(stock__gt=0)

    if brand_name:
        products = products.filter(brand__name__iexact=brand_name)  # Fixed

    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "home.html",
        {
            "products": page_obj,
            "categories": categories,
            "colors": colors,
            "materials": materials,
            "brands": brands,
        },
    )


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")


@login_required
def add_feedback(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.product = product
            feedback.customer = (
                request.user.customer
            )  # Assuming logged-in user is a customer
            feedback.save()
            messages.success(request, "Your feedback has been submitted successfully.")
            return redirect("view_orders")  # Redirect to product details
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FeedbackForm()

    return render(
        request, "customer/add_feedback.html", {"form": form, "product": product}
    )

@login_required(login_url="login")
def product_list(request):
    product_name = request.GET.get("product_name", "").strip()
    category = request.GET.get("category", "").strip()
    color = request.GET.get("color", "").strip()
    material = request.GET.get("material", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    in_stock = request.GET.get("in_stock")
    brand_name = request.GET.get("brand_name", "").strip()

    products = Product.objects.all().annotate(
        avg_rating=Avg('feedback__rating'),  # Average rating
        review_count=Count('feedback')  # Count total reviews
    )

    # Fetch distinct values for filtering
    categories = Product.objects.values_list("category", flat=True).distinct()
    colors = Product.objects.values_list("color", flat=True).distinct()
    materials = Product.objects.values_list("material", flat=True).distinct()
    brands = Product.objects.values_list("brand__brand_name", flat=True).distinct()  # Corrected

    # Apply Filters
    if product_name:
        products = products.filter(name__icontains=product_name)

    if category:
        products = products.filter(category__iexact=category)

    if material:
        products = products.filter(material__iexact=material)

    if color:
        products = products.filter(color__iexact=color)

    if min_price:
        try:
            min_price = float(min_price)
            products = products.filter(price__gte=min_price)
        except ValueError:
            pass  # Ignore invalid price values

    if max_price:
        try:
            max_price = float(max_price)
            products = products.filter(price__lte=max_price)
        except ValueError:
            pass

    if in_stock:
        products = products.filter(stock__gt=0)

    if brand_name:
        products = products.filter(brand__name__iexact=brand_name)  # Fixed

    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "customer/product_list.html",
        {
            "products": page_obj,
            "categories": categories,
            "colors": colors,
            "materials": materials,
            "brands": brands,
        },
    )
