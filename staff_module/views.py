from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator

from customer_module.models import Order
from .models import Staff
from .forms import OrderStatusUpdateForm, StaffRegistrationForm

def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        form = OrderStatusUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            # Display success message
            messages.success(request, "✅ Order status updated successfully!")
            return redirect('staff_dashboard')  # Redirect to orders page or appropriate URL
        else:
            messages.error(request, "❌ Failed to update order status. Please try again.")
    else:
        form = OrderStatusUpdateForm(instance=order)

    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'staff/update_order_status.html', context)

def staff_register(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash password
            user.role = 'staff'  # Assuming you have a 'role' field in your User model
            user.save()
            
            # Create Customer Profile
            Staff.objects.create(user=user)

            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = StaffRegistrationForm()

    return render(request, 'staff/register.html', {'form': form})

@login_required
def staff_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')

@login_required
def staff_home(request):
    orders = Order.objects.filter(is_delivered=False)
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'staff/staff_dashboard.html', {'orders': page_obj})


