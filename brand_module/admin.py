from django.contrib import admin

from .models import Brand, Product

# Register your models here.
@admin.register(Brand)
class brandAdmin(admin.ModelAdmin):
    list_display = ('brand_name', 'user', 'address', 'approval_status')
    list_filter = ('approval_status',)
    search_fields = ('brand_name', 'user__username', 'address')
admin.site.register(Product)