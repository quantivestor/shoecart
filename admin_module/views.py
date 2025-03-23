from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from brand_module.models import Brand, Product
from customer_module.models import Customer, Feedback
from staff_module.models import Staff

from .models import User


@staff_member_required
def admin_dashboard(request):
    return render(request, "admin/admin_dashboard.html")


@staff_member_required
def profile(request):
    return render(request, "admin/view_profile.html", {"profile": request.user})


@staff_member_required
def logout_view(request):
    logout(request)
    return redirect("home")


@staff_member_required
def review_brand_registrations(request):
    # Fetch all brand with pending approval status
    pending_brands = Brand.objects.filter(approval_status="pending")
    return render(
        request,
        "admin/review_brand_registrations.html",
        {"pending_brands": pending_brands},
    )


@staff_member_required
def approve_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.approval_status = "approved"
    brand.save()
    return redirect("review_brand_registrations")


@staff_member_required
def reject_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.approval_status = "rejected"
    brand.save()
    return redirect("review_brand_registrations")


@staff_member_required  # Restrict access to admin users
def list_brand_details(request):
    # Fetch all brands from the database
    brands = Brand.objects.all()
    return render(request, "admin/brand_list.html", {"brands": brands})


@staff_member_required  # Restrict access to admin users
def list_customer_details(request):
    # Fetch all customers from the database
    customers = Customer.objects.all()
    return render(request, "admin/customer_list.html", {"customers": customers})


@staff_member_required
def delete_brand(request, brand_id):
    brand = get_object_or_404(brand, id=brand_id)
    user = brand.user
    brand.delete()
    user.delete()
    messages.success(request, "Brand deleted successfully.")
    return redirect("list_brand_details")


@staff_member_required
def delete_customer(request, cus_id):
    customer = get_object_or_404(Customer, id=cus_id)
    user = customer.user
    customer.delete()
    user.delete()
    messages.success(request, "Customer deleted successfully.")
    return redirect("list_customer_details")


@staff_member_required
def review_staff_registrations(request):
    # Fetch all staff with pending approval status
    pending_staffs = Staff.objects.filter(approval_status="pending")
    return render(
        request,
        "admin/review_staff_registrations.html",
        {"pending_staffs": pending_staffs},
    )


@staff_member_required
def approve_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    staff.approval_status = "approved"
    staff.save()
    return redirect("review_staff_registrations")


@staff_member_required
def reject_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    staff.approval_status = "rejected"
    staff.save()
    return redirect("review_staff_registrations")


@staff_member_required  # Restrict access to admin users
def list_staff_details(request):
    # Fetch all staff from the database
    staffs = Staff.objects.all()
    return render(request, "admin/staff_list.html", {"staffs": staffs})

@staff_member_required
def delete_staff(request, cus_id):
    staff = get_object_or_404(Staff, id=cus_id)
    user = staff.user
    staff.delete()
    user.delete()
    messages.success(request, "Staff deleted successfully.")
    return redirect("list_staff_details")


def home(request):
    product_name = request.GET.get("product_name", "")

    # New Filters
    category = request.GET.get("category", "")
    color = request.GET.get("color", "")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    in_stock = request.GET.get("in_stock")

    products = Product.objects.all()
    categories = Product.objects.values_list("category", flat=True).distinct()
    colors = Product.objects.values_list("color", flat=True).distinct()

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
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "home.html",
        {"products": page_obj, "categories": categories, "colors": colors},
    )


def userlogin(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Authenticate the user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Check if the user is linked to a brand
            try:
                if user.role == "brand":
                    brand = user.brand  # Access the linked brand object
                    if (
                        brand.approval_status == "approved"
                    ):  # Check if the brand is approved
                        login(request, user)  # Log in the user

                        # Store brand_id in session
                        request.session["brand_id"] = brand.id

                        return redirect(
                            "brand_dashboard"
                        )  # Redirect to the brand dashboard
                    else:
                        messages.error(
                            request,
                            "Your brand registration is still pending or has been rejected.",
                        )
                elif user.role == "customer":
                    customer = user.customer  # Access the linked Customer object
                    login(request, user)  # Log in the user

                    # Store salon_id in session
                    request.session["customer_id"] = customer.id

                    return redirect("product_list")  # Redirect to the customer dashboard
                elif user.is_staff:
                    login(request, user)  # Log in the staff member
                    return redirect("admin_dashboard")

                elif user.role == "staff":
                    staff = user.staff  # Access the linked brand object
                    if (
                        staff.approval_status == "approved"
                    ):
                        login(request, user)
                        return redirect("staff_dashboard")
                    else:
                        messages.error(
                            request,
                            "Your registration is still pending or has been rejected.",
                        )

            except User.DoesNotExist:
                messages.error(request, "No account.")
        else:
            messages.error(request, "Invalid email or password.")

        return redirect("home")

    elif request.method == "GET":
        return render(request, "login.html")
    
@staff_member_required
def view_feedbacks(request):
    feedbacks = Feedback.objects.all().order_by("-added_at")
    return render(request, "admin/view_feedbacks.html", {"feedbacks": feedbacks})
