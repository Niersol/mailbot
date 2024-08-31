from django.contrib import admin

from .models import *
# Register your models here.
@admin.register(Order)
class adminOrder(admin.ModelAdmin):
    pass
@admin.register(Product)
class adminProduct(admin.ModelAdmin):
    pass
@admin.register(Customer)
class adminCustomer(admin.ModelAdmin):
    pass
@admin.register(GiftCard)
class adminGiftCard(admin.ModelAdmin):
    pass