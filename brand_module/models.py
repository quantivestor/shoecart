from django.contrib.gis.db import models

from admin_module.models import User


# Create your models here.
class Brand(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="brand"
    )  # Link to the User model
    brand_name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    contact_info = models.CharField(max_length=15)
    approval_status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.brand_name

    def set_password(self, raw_password):
        self.user.set_password(raw_password)  # Set password for the linked User
        self.user.save()

    def check_password(self, raw_password):
        return self.user.check_password(raw_password)


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("casual", "Casual"),
        ("formal", "Formal"),
    ]

    MATERIAL_CHOICES = [
        ("leather", "Leather"),
        ("cotton", "Cotton"),
    ]

    COLOR_CHOICES = [
        ("black", "Black"),
        ("white", "White"),
        ("grey", "Grey"),
        ("red", "Red"),
    ]

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=1)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    material = models.CharField(max_length=100, choices=MATERIAL_CHOICES)
    color = models.CharField(max_length=100, choices=COLOR_CHOICES)
    left_image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    straight_image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    right_image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    sizes = models.CharField(
        max_length=100, help_text="Comma-separated sizes, e.g., S,M,L,XL"
    )
    offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def discounted_price(self):
        """Calculate discounted price based on offer percentage"""
        if self.offer_percentage > 0:
            discount_amount = (self.price * self.offer_percentage) / 100
            return round(self.price - discount_amount, 2)
        return self.price

    def get_size_list(self):
        return self.sizes.split(",") if self.sizes else []

    def __str__(self):
        return self.name
