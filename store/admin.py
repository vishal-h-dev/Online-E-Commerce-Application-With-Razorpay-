from django.contrib import admin
from .models import (
    CustomerProfile, PhoneNumber, Address,
    Category, Brand, Product, Review,
    Cart, CartItem, Wishlist, WishlistItem,
    Order, OrderItem
)

admin.site.register(CustomerProfile)
admin.site.register(PhoneNumber)
admin.site.register(Address)
admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Wishlist)
admin.site.register(WishlistItem)
admin.site.register(Order)
admin.site.register(OrderItem)
from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'active', 'valid_from', 'valid_to')
    list_filter = ('active',)
    search_fields = ('code',)