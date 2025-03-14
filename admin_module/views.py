from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout

from .models import User
from customer_module.models import Customer
from shop_module.models import Shop


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
def review_shop_registrations(request):
    # Fetch all salons with pending approval status
    pending_shops = Shop.objects.filter(approval_status='pending')
    return render(request, 'admin/review_shop_registrations.html', {'pending_shops': pending_shops})

@staff_member_required
def approve_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    shop.approval_status = 'approved'
    shop.save()
    return redirect('review_shop_registrations')

@staff_member_required
def reject_shop(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    shop.approval_status = 'rejected'
    shop.save()
    return redirect('review_salon_registrations')

@staff_member_required  # Restrict access to admin users
def list_shop_details(request):
    # Fetch all salons from the database
    shops = Shop.objects.all()
    return render(request, 'admin/shop_list.html', {'shops': shops})

@staff_member_required  # Restrict access to admin users
def list_customer_details(request):
    # Fetch all customers from the database
    customers = Customer.objects.all()
    return render(request, 'admin/customer_list.html', {'customers': customers})

@staff_member_required
def delete_shop(request, shop_id):
    shop = get_object_or_404(shop, id=shop_id)
    user = shop.user
    shop.delete()
    user.delete()
    messages.success(request, "Shop deleted successfully.")
    return redirect('list_shop_details')

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
            # Check if the user is linked to a shop
            try:
                if user.role == "shop":
                    shop = user.shop  # Access the linked shop object
                    if shop.approval_status == 'approved':  # Check if the shop is approved
                        login(request, user)  # Log in the user

                       # Store shop_id in session
                        request.session['shop_id'] = shop.id

                        return redirect('shop_dashboard')  # Redirect to the shop dashboard
                    else:
                        messages.error(request, 'Your shop registration is still pending or has been rejected.')
                elif user.role == "customer":
                    customer = user.customer  # Access the linked Customer object
                    login(request, user)  # Log in the user

                    # Store salon_id in session
                    request.session['customer_id'] = customer.id
                    
                    return redirect('user_home')  # Redirect to the customer dashboard
                elif user.is_staff:
                    login(request, user)  # Log in the staff member
                    return redirect('admin_dashboard')
                
            except User.DoesNotExist:
                messages.error(request, 'No account.')
        else:
            messages.error(request, 'Invalid email or password.')
    return redirect('home')