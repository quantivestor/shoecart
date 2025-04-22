from django.conf import settings
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

import cv2
import numpy as np
import mediapipe as mp
from django.http import StreamingHttpResponse
from django.shortcuts import render
from PIL import Image
import os

from brand_module.models import Product
from ShoeCart.settings import EMAIL_HOST_USER

from .forms import CustomerRegistrationForm, FeedbackForm, UserProfileForm
from .models import Cart, Customer, Feedback, Order, Transaction


@login_required(login_url="login")
def user_profile(request):
    customer = request.user.customer

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect("product_list")
    else:
        form = UserProfileForm(instance=customer)

    return render(request, "customer/profile.html", {"form": form})

@login_required(login_url="login")
def view_feedbacks(request, product_id):
    # Filter feedbacks for product
    product = get_object_or_404(Product, id=product_id)
    feedbacks = Feedback.objects.filter(
        order__product=product
    ).select_related("order", "customer")

    return render(
        request,
        "customer/view_feedbacks.html",
        {
            "feedbacks": feedbacks,
        },
    )

@login_required(login_url="login")
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    size = request.POST.get("size", None)

    if not size:
        messages.error(request, "Please select a size before adding to cart.")
        return redirect("product_list")
    
    if product.stock < 1:
        messages.error(
            request, f"Insufficient stock for {product.name}."
        )
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
@login_required(login_url="login")
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
@login_required(login_url="login")
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user.customer)
    cart_item.delete()
    return redirect("view_cart")


@login_required(login_url="login")
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


@login_required(login_url="login")
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

@login_required(login_url="login")
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

@login_required(login_url="login")
def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user.customer)

    # Restock product
    order.product.stock += order.quantity
    order.product.save()

    # Update order status to 'Cancelled'
    order.status = "Returned"
    order.track_status = "Ready To Pickup"
    order.is_delivered = False
    order.save()

    transaction = Transaction.objects.get(order=order)
    transaction.status = "Refunded"
    transaction.save()

    send_mail(
        "Order Return Request Accepted",
        f"Dear {order.user.user.username},\n\n"
        f"A refund of ₹{order.total_amount} has been processed.\n\n"
        "Thank you for shopping with us!",
        EMAIL_HOST_USER,
        [order.user.user.email],
        fail_silently=False,
    )

    messages.success(
        request,
        f"Order Return Request Accepted.",
    )
    return redirect("view_orders")


# View Orders
@login_required(login_url="login")
def view_orders(request):
    feedback_subquery = Feedback.objects.filter(
        order=OuterRef("id"), customer=request.user.customer
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
@login_required(login_url="login")
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
                foot_video=form.cleaned_data["foot_video"],  # Correct way to retrieve image
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
    gender = request.GET.get("gender", "").strip()
    material = request.GET.get("material", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    in_stock = request.GET.get("in_stock")
    brand_name = request.GET.get("brand_name", "").strip()

    products = Product.objects.all().annotate(
        avg_rating=Avg('order__feedback__rating'),  # Average rating
        review_count=Count('order__feedback')  # Count total reviews
    )

    # Fetch distinct values for filtering
    categories = Product.objects.values_list("category", flat=True).distinct()
    colors = Product.objects.values_list("color", flat=True).distinct()
    materials = Product.objects.values_list("material", flat=True).distinct()
    genders = Product.objects.values_list("gender", flat=True).distinct()
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

    if gender:
        products = products.filter(gender__iexact=gender)

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
            "genders": genders
        },
    )


@login_required(login_url="login")
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("login")


@login_required(login_url="login")
def add_feedback(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.order = order
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
        request, "customer/add_feedback.html", {"form": form, "product": order.product}
    )

@login_required(login_url="login")
def product_list(request):
    product_name = request.GET.get("product_name", "").strip()
    category = request.GET.get("category", "").strip()
    color = request.GET.get("color", "").strip()
    gender = request.GET.get("gender", "").strip()
    material = request.GET.get("material", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    in_stock = request.GET.get("in_stock")
    brand_name = request.GET.get("brand", "").strip()

    products = Product.objects.all().annotate(
        avg_rating=Avg('order__feedback__rating'),  # Average rating
        review_count=Count('order__feedback')  # Count total reviews
    )

    # Fetch distinct values for filtering
    categories = Product.objects.values_list("category", flat=True).distinct()
    colors = Product.objects.values_list("color", flat=True).distinct()
    genders = Product.objects.values_list("gender", flat=True).distinct()
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

    if gender:
        products = products.filter(gender__iexact=gender)

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
        products = products.filter(brand__brand_name__iexact=brand_name)  # Fixed

    # Pagination
    paginator = Paginator(products, 12)
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
            "genders": genders,
        },
    )


# AI Integration
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def load_shoe_image(shoe_path):
    """Load the shoe image or return a default shoe."""
    if os.path.exists(shoe_path):
        shoe_img = Image.open(shoe_path).convert('RGBA')
        return np.array(shoe_img)
    return np.zeros((100, 200, 4), dtype=np.uint8)  # Default transparent image

def overlay_image(background, foreground, x_offset, y_offset, scale=1.0):
    """Overlay a foreground image onto a background image."""
    h, w = foreground.shape[:2]
    foreground_resized = cv2.resize(foreground, (int(w * scale), int(h * scale)))
    h_resized, w_resized = foreground_resized.shape[:2]

    y1, y2 = max(0, y_offset), min(background.shape[0], y_offset + h_resized)
    x1, x2 = max(0, x_offset), min(background.shape[1], x_offset + w_resized)

    alpha = foreground_resized[:, :, 3] / 255.0
    alpha = np.expand_dims(alpha, axis=-1)
    fg_section = foreground_resized[:, :, :3]

    bg_section = background[y1:y2, x1:x2]
    blended = bg_section * (1 - alpha) + fg_section * alpha
    background[y1:y2, x1:x2] = blended.astype(np.uint8)
    return background

def generate_frames(video_path, shoe_path):
    cap = cv2.VideoCapture(video_path)
    shoe_img = load_shoe_image(shoe_path)
    shoe_scale = 0.3

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        output_frame = frame.copy()

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

            for ankle in [left_ankle, right_ankle]:
                if ankle.visibility > 0.5:
                    x_offset = int(ankle.x * frame.shape[1])
                    y_offset = int(ankle.y * frame.shape[0])
                    output_frame = overlay_image(output_frame, shoe_img, x_offset, y_offset, shoe_scale)
        
        _, buffer = cv2.imencode('.jpg', output_frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()
    cv2.destroyAllWindows()




class SimpleVirtualShoeTryOn:
    def __init__(self, video_path, shoe_path):
        # Initialize MediaPipe Pose for foot tracking
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Load the video
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video at {video_path}")
        
        # Get video properties
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # Load the shoe image or use default PNG
        self.shoe_img = self.load_shoe_file(shoe_path)
        
        # Initial shoe properties
        self.shoe_scale = 0.3  # Initial scale, adjust as needed
        self.x_offset_factor = 0.2  # Added x-offset factor
        self.y_offset_factor = 0.2  # Added y-offset factor
        
        self.shoe_height = self.shoe_img.shape[0]
        self.shoe_width = self.shoe_img.shape[1]
        
    
    def load_shoe_file(self, shoe_path):
        """Load shoe file - handle both images and OBJ files"""
        # Default PNG path - either use provided one or embedded one
        default_png_path = "default_shoe.png"
        
        _, file_extension = os.path.splitext(shoe_path)
        
        if file_extension.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.bmp']:
            # It's an image file
            try:
                shoe_img = Image.open(shoe_path)
                if shoe_img.mode != 'RGBA':
                    shoe_img = shoe_img.convert('RGBA')
                return np.array(shoe_img)
            except Exception as e:
                print(f"Error loading image file: {e}")
                print("Using default shoe image instead.")
        
        # For OBJ files or if image loading failed, try to use a default PNG
        print(f"Not using {shoe_path} - using a default PNG shoe image instead.")
        
        # First check if default_shoe.png exists in the current directory
        if os.path.exists(default_png_path):
            try:
                shoe_img = Image.open(default_png_path)
                if shoe_img.mode != 'RGBA':
                    shoe_img = shoe_img.convert('RGBA')
                return np.array(shoe_img)
            except Exception as e:
                print(f"Error loading default image: {e}")
        
        # If we get here, we need to create a basic shoe image
        return self.create_default_shoe_image()
    
    def create_default_shoe_image(self):
        """Create a basic shoe silhouette as a fallback"""
        # Create a transparent canvas
        img = np.zeros((300, 600, 4), dtype=np.uint8)
        
        # Draw a simple shoe silhouette
        # Shoe body
        pts = np.array([
            [150, 150], [500, 150], [550, 180], [500, 200],
            [250, 200], [200, 220], [150, 220], [100, 200], [100, 180]
        ], np.int32)
        pts = pts.reshape((-1, 1, 2))
        
        # Fill the shoe with color
        cv2.fillPoly(img, [pts], (139, 69, 19, 255))  # Brown with full opacity
        
        # Add some details
        cv2.ellipse(img, (350, 175), (100, 25), 0, 0, 360, (101, 67, 33, 255), -1)
        
        # Save this image for future use
        cv2.imwrite("default_shoe.png", img)
        
        return img
    
    def overlay_image(self, background, foreground, x_offset, y_offset, scale=1.0):
        """Overlay a foreground RGBA image onto a background image at the specified position with scaling"""
        # Scale the foreground image
        h, w = foreground.shape[:2]
        foreground_scaled = cv2.resize(
            foreground, 
            (int(w * scale), int(h * scale)), 
            interpolation=cv2.INTER_AREA
        )
        h_scaled, w_scaled = foreground_scaled.shape[:2]
        
        # Calculate positioning
        y1 = max(0, y_offset)
        y2 = min(background.shape[0], y_offset + h_scaled)
        x1 = max(0, x_offset)
        x2 = min(background.shape[1], x_offset + w_scaled)
        
        # Adjust overlay image positioning
        y1_overlay = max(0, -y_offset)
        y2_overlay = h_scaled - max(0, y_offset + h_scaled - background.shape[0])
        x1_overlay = max(0, -x_offset)
        x2_overlay = w_scaled - max(0, x_offset + w_scaled - background.shape[1])
        
        # Check if there's a valid overlay area
        if y1 >= y2 or x1 >= x2 or y1_overlay >= y2_overlay or x1_overlay >= x2_overlay:
            return background
        
        # Get alpha channel
        alpha = foreground_scaled[y1_overlay:y2_overlay, x1_overlay:x2_overlay, 3] / 255.0
        alpha = np.expand_dims(alpha, axis=-1)
        
        # Convert foreground from RGBA to BGR (OpenCV uses BGR)
        # This is critical to maintain the correct color
        fg_section = foreground_scaled[y1_overlay:y2_overlay, x1_overlay:x2_overlay, :3]
        
        # OpenCV loads images as RGB but displays as BGR, so we need to flip channels
        # if the foreground was loaded with PIL or another RGB-based library
        fg_section = cv2.cvtColor(fg_section, cv2.COLOR_RGB2BGR)
        
        # Apply alpha blending
        try:
            bg_section = background[y1:y2, x1:x2]
            blended = bg_section * (1 - alpha) + fg_section * alpha
            background[y1:y2, x1:x2] = blended.astype(np.uint8)
        except Exception as e:
            print(f"Error during overlay: {e}")
        
        return background
    
    def process_frame(self, frame):
        """Process video frame to detect feet and overlay shoe images"""
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        res = False
        
        output_frame = frame.copy()
        
        if results.pose_landmarks:
            res = True
            landmarks = results.pose_landmarks.landmark
            
            # Get ankle positions
            left_ankle = landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE]
            right_ankle = landmarks[self.mp_pose.PoseLandmark.RIGHT_ANKLE]
            left_heel = landmarks[self.mp_pose.PoseLandmark.LEFT_HEEL]
            right_heel = landmarks[self.mp_pose.PoseLandmark.RIGHT_HEEL]
            left_foot_index = landmarks[self.mp_pose.PoseLandmark.LEFT_FOOT_INDEX]
            right_foot_index = landmarks[self.mp_pose.PoseLandmark.RIGHT_FOOT_INDEX]
            
            # Determine foot orientation and choose which foot/feet are visible
            for side, (ankle, heel, foot_index) in enumerate([
                (left_ankle, left_heel, left_foot_index),
                (right_ankle, right_heel, right_foot_index)
            ]):
                # Check if this foot is visible enough
                if ankle.visibility > 0.5:
                    # Calculate the foot orientation angle
                    if heel.visibility > 0.5 and foot_index.visibility > 1:
                        dx = foot_index.x - heel.x
                        dy = foot_index.y - heel.y
                        angle = np.degrees(np.arctan2(dy, dx))
                    else:
                        angle = 0  # Default angle if we can't calculate
                    
                    # Get pixel coordinates
                    ankle_x = int(ankle.x * self.width)
                    ankle_y = int(ankle.y * self.height)
                    
                    # Flip the shoe image for the right foot
                    shoe_img_to_use = self.shoe_img.copy()
                    
                    
                    # Apply rotation if needed
                    if abs(angle) > 30:  # Only rotate if the angle is significant
                        # Get center of the shoe
                        center = (self.shoe_width // 2, self.shoe_height // 2)
                        
                        # Get rotation matrix
                        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
                        
                        # Rotate the shoe image
                        shoe_img_to_use = cv2.warpAffine(
                            shoe_img_to_use, 
                            rot_mat, 
                            (self.shoe_width, self.shoe_height), 
                            flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_TRANSPARENT
                        )
                    
                    # Calculate placement position using the offset factors
                    x_offset = ankle_x - int(self.shoe_width * self.shoe_scale * self.x_offset_factor)
                    y_offset = ankle_y - int(self.shoe_height * self.shoe_scale * self.y_offset_factor)
                    
                    # Overlay the shoe on the frame
                    output_frame = self.overlay_image(
                        output_frame, 
                        shoe_img_to_use, 
                        x_offset, 
                        y_offset, 
                        self.shoe_scale
                    )
        
    
        return output_frame,res
    
    def run(self):
        """Run the virtual shoe try-on application"""
        i = 1
        while self.cap.isOpened():
            if i <5:
                ret, frame = self.cap.read()
            if not ret:
                # If the video ended, loop back to the beginning
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            # Process the frame
            output_frame,res = self.process_frame(frame)
            if res:
                i+=1

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # q or ESC key
                    break
                elif key == ord('+') or key == ord('='):
                    self.shoe_scale += 0.05
                    print(f"Shoe scale: {self.shoe_scale:.2f}")
                elif key == ord('-') or key == ord('_'):
                    self.shoe_scale = max(0.1, self.shoe_scale - 0.05)
                    print(f"Shoe scale: {self.shoe_scale:.2f}")
                _, buffer = cv2.imencode('.jpg', output_frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()



def shoe_tryon_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    customer = request.user.customer
    video_path = video_path = os.path.join(settings.MEDIA_ROOT, str(customer.foot_video)) # Replace with actual path
    shoe_path = os.path.join(settings.MEDIA_ROOT, str(product.right_image)) # Replace with actual path
    app = SimpleVirtualShoeTryOn(video_path, shoe_path)
    return StreamingHttpResponse(app.run(), content_type='multipart/x-mixed-replace; boundary=frame')