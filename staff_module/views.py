from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import send_mail

from ShoeCart.settings import EMAIL_HOST_USER
from customer_module.models import Order

from .forms import OrderStatusUpdateForm, StaffRegistrationForm
from .models import Staff


def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        form = OrderStatusUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            # Display success message
            messages.success(request, "✅ Order status updated successfully!")

            if form.cleaned_data.get("track_status", "") == "Out For Delivery":
                send_mail(
                    "Arriving Today",
                    f"Dear {order.user.user.username},\n\n"
                    f"Your order for {order.product.name} is out for delivery.\n\n"
                    "Thank you for shopping with us!",
                    EMAIL_HOST_USER,
                    [order.user.user.email],
                    fail_silently=False,
                )

            return redirect(
                "staff_dashboard"
            )  # Redirect to orders page or appropriate URL
        else:
            messages.error(
                request, "❌ Failed to update order status. Please try again."
            )
    else:
        form = OrderStatusUpdateForm(instance=order)

    context = {
        "form": form,
        "order": order,
    }
    return render(request, "staff/update_order_status.html", context)


def staff_register(request):
    if request.method == "POST":
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])  # Hash password
            user.role = "staff"  # Assuming you have a 'role' field in your User model
            user.save()

            # Create Customer Profile
            Staff.objects.create(user=user, phone_number=form.cleaned_data["phone_number"])

            messages.success(request, "Registration successful. Please log in.")
            return redirect("login")
    else:
        form = StaffRegistrationForm()

    return render(request, "staff/register.html", {"form": form})


@login_required(login_url="login")
def staff_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")


@login_required(login_url="login")
def staff_home(request):
    orders = Order.objects.filter(is_delivered=False).exclude(status="Cancelled")
    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "staff/staff_dashboard.html", {"orders": page_obj})
