from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout

from .models import User
from customer_module.models import Customer
from brand_module.models import Brand


@staff_member_required
def admin_dashboard(request):
    return render(request, 'admin/admin_dashboard.html')

@staff_member_required
def profile(request):
    return render(request, 'admin/view_profile.html', {'profile': request.user})

@staff_member_required
def logout_view(request):
    logout(request)
    return redirect('home')

@staff_member_required
def review_brand_registrations(request):
    # Fetch all salons with pending approval status
    pending_brands = Brand.objects.filter(approval_status='pending')
    return render(request, 'admin/review_brand_registrations.html', {'pending_brands': pending_brands})

@staff_member_required
def approve_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.approval_status = 'approved'
    brand.save()
    return redirect('review_brand_registrations')

@staff_member_required
def reject_brand(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.approval_status = 'rejected'
    brand.save()
    return redirect('review_salon_registrations')

@staff_member_required  # Restrict access to admin users
def list_brand_details(request):
    # Fetch all salons from the database
    brands = Brand.objects.all()
    return render(request, 'admin/brand_list.html', {'brands': brands})

@staff_member_required  # Restrict access to admin users
def list_customer_details(request):
    # Fetch all customers from the database
    customers = Customer.objects.all()
    return render(request, 'admin/customer_list.html', {'customers': customers})

@staff_member_required
def delete_brand(request, brand_id):
    brand = get_object_or_404(brand, id=brand_id)
    user = brand.user
    brand.delete()
    user.delete()
    messages.success(request, "Brand deleted successfully.")
    return redirect('list_brand_details')

@staff_member_required
def delete_customer(request, cus_id):
    customer = get_object_or_404(Customer, id=cus_id)
    user = customer.user
    customer.delete()
    user.delete()
    messages.success(request, "Customer deleted successfully.")
    return redirect('list_customer_details')

def home(request):
    return render(request, 'home.html')

def userlogin(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Check if the user is linked to a brand
            try:
                if user.role == "brand":
                    brand = user.brand  # Access the linked brand object
                    if brand.approval_status == 'approved':  # Check if the brand is approved
                        login(request, user)  # Log in the user

                       # Store brand_id in session
                        request.session['brand_id'] = brand.id

                        return redirect('brand_dashboard')  # Redirect to the brand dashboard
                    else:
                        messages.error(request, 'Your brand registration is still pending or has been rejected.')
                elif user.role == "customer":
                    customer = user.customer  # Access the linked Customer object
                    login(request, user)  # Log in the user

                    # Store salon_id in session
                    request.session['customer_id'] = customer.id
                    
                    return redirect('user_home')  # Redirect to the customer dashboard
                elif user.is_staff:
                    login(request, user)  # Log in the staff member
                    return redirect('admin_dashboard')
                
                elif user.role == 'staff':
                    login(request, user)
                    return redirect('staff_dashboard')
                
            except User.DoesNotExist:
                messages.error(request, 'No account.')
        else:
            messages.error(request, 'Invalid email or password.')
    return redirect('home')