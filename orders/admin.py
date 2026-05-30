from django.contrib import admin

from orders.models import Order, OrderStatus


class OrderStatusInline(admin.TabularInline):
    model = OrderStatus
    extra = 0
    readonly_fields = ("changed_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "pickup_address", "dropoff_address", "status", "pickup_time", "created_at")
    list_filter = ("status", "tariff")
    search_fields = ("phone", "pickup_address", "dropoff_address", "client__full_name")
    inlines = [OrderStatusInline]


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ("order", "status", "changed_by", "changed_at")
    list_filter = ("status",)
