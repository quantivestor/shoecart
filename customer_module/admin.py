from django.contrib import admin

from .models import Cart, Customer, Feedback, Order, Transaction

# Register your models here.
admin.site.register(Customer)
admin.site.register(Feedback)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(Transaction)
