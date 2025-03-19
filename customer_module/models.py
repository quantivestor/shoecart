from django.db import models

from admin_module.models import User
from brand_module.models import Product as Product


# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer")
    phone_number = models.CharField(max_length=15)
    left_image = models.ImageField(upload_to="foot_images/", null=True, blank=True)
    straight_image = models.ImageField(upload_to="foot_images/", null=True, blank=True)
    right_image = models.ImageField(upload_to="foot_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Feedback(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.product.name}"


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
        max_length=100, null=True, blank=True, default="Ready to dispatch"
    )
    is_delivered = models.BooleanField(default=False)

    def __str__(self):
        return f"Order by {self.user.user.username} for {self.product.name}"


class Transaction(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="transaction_set"
    )
    payment_id = models.CharField(max_length=100, unique=True)  # Reference ID
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=[("Pending", "Pending"), ("Completed", "Completed")],
        default="Pending",
    )
    card_number = models.IntegerField(null=False, blank=False)
    card_expiry = models.CharField(max_length=10, null=False, blank=False)
    card_cvv = models.IntegerField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.payment_id} - {self.status}"
