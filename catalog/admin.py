from django.contrib import admin

from catalog.models import Tariff, Vehicle


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_km", "minimum_price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("license_plate", "brand", "model", "status")
    list_filter = ("status",)
    search_fields = ("license_plate", "brand", "model")
