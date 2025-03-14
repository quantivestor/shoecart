from django.contrib.gis.db import models

from admin_module.models import User

# Create your models here.
class Shop(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop')  # Link to the User model
    shop_name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    point = models.PointField()
    contact_info = models.CharField(max_length=15)
    approval_status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shop_name

    def set_password(self, raw_password):
        self.user.set_password(raw_password)  # Set password for the linked User
        self.user.save()

    def check_password(self, raw_password):
        return self.user.check_password(raw_password)
    

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('fashion', 'Fashion'),
        ('grocery', 'Grocery'),
        ('home_appliances', 'Home Appliances'),
        ('sports', 'Sports'),
        ('books', 'Books'),
        ('beauty', 'Beauty'),
        ('health', 'Health'),
        ('toys', 'Toys'),
    ]


    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name