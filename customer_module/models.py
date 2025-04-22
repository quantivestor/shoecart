from django.db import models

from admin_module.models import User
from brand_module.models import Product as Product


# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer")
    phone_number = models.CharField(max_length=15, unique=True)
    foot_video = models.FileField(upload_to="foot_videos/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Cart(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} in {self.user.user.username}'s cart"


class Order(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Refunded", "Refunded"),
        ("Returned", "Returned"),
    ]

    TRACK_STATUS_CHOICES = [
        ("Ready to Dispatch", "Ready to Dispatch"),
        ("Shipped", "Shipped"),
        ("Reached on Nearest Hub", "Reached on Nearest Hub"),
        ("Out For Delivery", "Out For Delivery"),
        ("Delivered", "Delivered"),
        ("Ready To Pickup", "Ready To Pickup"),
        ("Pickedup", "Pickedup")
    ]
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    size = models.CharField(max_length=10, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField(null=False, blank=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    ordered_at = models.DateTimeField(auto_now_add=True)
    track_status = models.CharField(
        max_length=100, null=True, blank=True, choices=TRACK_STATUS_CHOICES, default="Ready to dispatch"
    )
    is_delivered = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_delivered:
            self.track_status = "Delivered"
            if self.status not in ["Delivered", "Cancelled", "Refunded"]:
                self.status = "Delivered"  # Update only if not already delivered/cancelled
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} Order by {self.user.user.username} for {self.product.name}"
    

class Feedback(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.order.product.name}"


class Transaction(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="transaction_set"
    )
    payment_id = models.CharField(max_length=100, unique=True)  # Reference ID
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=[("Pending", "Pending"), ("Completed", "Completed"), ("Refunded", "Refunded")],
        default="Pending",
    )
    card_number = models.IntegerField(null=False, blank=False)
    card_expiry = models.CharField(max_length=10, null=False, blank=False)
    card_cvv = models.IntegerField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.payment_id} - {self.status}"
