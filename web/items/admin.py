from django.contrib import admin
from .models import Item, Order, OrderItems, Coupon, PromotionCode, Tax

admin.site.register(Item)

class OrderItemsInline(admin.TabularInline):
    model = OrderItems
    extra = 0
    
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemsInline,]

admin.site.register(Order, OrderAdmin)
admin.site.register(Coupon)
admin.site.register(PromotionCode)
admin.site.register(Tax)