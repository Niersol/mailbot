from django.contrib import admin
from .models import *
# Register your models here.
@admin.register(Conversation)
class adminConversation(admin.ModelAdmin):
    pass

@admin.register(Message)
class adminMessage(admin.ModelAdmin):
    pass

@admin.register(Product)
class adminProduct(admin.ModelAdmin):
    pass

@admin.register(Category)
class adminCategory(admin.ModelAdmin):
    pass

@admin.register(Collection)
class adminCollection(admin.ModelAdmin):
    pass

@admin.register(Cart)
class adminCart(admin.ModelAdmin):
    pass

@admin.register(CartItem)
class adminCartItem(admin.ModelAdmin):
    pass

@admin.register(Order)
class adminOrder(admin.ModelAdmin):
    pass

@admin.register(OrderItem)
class adminOrderItem(admin.ModelAdmin):
    pass