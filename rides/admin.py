from django.contrib import admin

from rides.models import Driver, DriverReview, Ride, Tariff


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ("user", "from_address", "to_address", "status", "price", "created_at")
    list_filter = ("status", "tariff")
    search_fields = ("user__phone", "user__username", "from_address", "to_address")


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_km", "min_price", "description")


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("name", "car", "plate", "rating", "is_active")


@admin.register(DriverReview)
class DriverReviewAdmin(admin.ModelAdmin):
    list_display = ("ride", "rating")
