from django.contrib import admin

from .models import Shop, Product

# Register your models here.
@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'user', 'address', 'approval_status')
    list_filter = ('approval_status',)
    search_fields = ('shop_name', 'user__username', 'address')
admin.site.register(Product)