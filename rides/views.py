from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.templatetags.static import static
from django.views.decorators.http import require_POST

from rides.forms import DriverReviewForm, RideOrderForm
from rides.models import DriverReview, Ride, Tariff
from rides.utils import assign_driver, calculate_ride_price


def index(request):
    tariffs = Tariff.objects.all()
    tariff_car_map = {
        "Эконом": ["Volkswagen Polo", "Hyundai Solaris", "Kia Rio"],
        "Комфорт": ["Toyota Camry", "Kia K5", "Hyundai Sonata"],
        "Бизнес": ["Mercedes-Benz E-Class", "BMW 5 Series", "Audi A6"],
    }
    tariffs_with_cars = [
        {
            "tariff": tariff,
            "cars": tariff_car_map.get(tariff.name, ["Автомобили подбираются по доступности"]),
        }
        for tariff in tariffs
    ]
    return render(request, "rides/index.html", {"tariffs_with_cars": tariffs_with_cars, "tariffs": tariffs})


@login_required
def order_ride(request):
    if request.method == "POST":
        form = RideOrderForm(request.POST)
        if form.is_valid():
            ride = form.save(commit=False)
            ride.user = request.user

            tariff = ride.tariff
            distance = Decimal(str(form.cleaned_data["distance_km"]))
            calculated_price = calculate_ride_price(distance, tariff)

            driver = assign_driver(tariff)
            ride.distance_km = float(distance)
            ride.price = calculated_price
            ride.driver_name = driver["name"]
            ride.driver_car = driver["car"]
            ride.driver_plate = driver["plate"]
            ride.status = "searching"
            ride.save()

            messages.success(request, "Заказ создан. Мы ищем водителя.")
            return redirect("rides:ride_status", pk=ride.pk)
        messages.error(request, "Не удалось создать поездку. Проверьте форму.")
    else:
        initial = {
            "from_address": request.GET.get("from_address", ""),
            "to_address": request.GET.get("to_address", ""),
            "tariff": request.GET.get("tariff", ""),
        }
        form = RideOrderForm(initial=initial)

    tariffs_json = [
        {
            "id": tariff.id,
            "name": tariff.name,
            "price_per_km": str(tariff.price_per_km),
            "min_price": str(tariff.min_price),
        }
        for tariff in Tariff.objects.all()
    ]
    return render(
        request,
        "rides/order.html",
        {
            "form": form,
            "tariffs_json": tariffs_json,
            "yandex_maps_api_key": settings.YANDEX_MAPS_API_KEY,
        },
    )


def ride_status(request, pk):
    ride = get_object_or_404(Ride, pk=pk)
    review_form = DriverReviewForm()
    tracking_payload = {
        "rideId": ride.pk,
        "status": ride.status,
        "fromAddress": ride.from_address,
        "toAddress": ride.to_address,
        "driverName": ride.driver_name or "Водитель",
        "completeUrl": reverse("rides:complete_demo_ride", kwargs={"pk": ride.pk}),
        "carIconUrl": static("img/car-marker.svg"),
    }
    return render(
        request,
        "rides/ride_status.html",
        {
            "ride": ride,
            "review_form": review_form,
            "yandex_maps_api_key": settings.YANDEX_MAPS_API_KEY,
            "tracking_payload": tracking_payload,
        },
    )


@login_required
def rate_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk, user=request.user)
    if request.method != "POST":
        return redirect("rides:ride_status", pk=ride.pk)

    if ride.status != "completed":
        messages.error(request, "Оценить можно только завершенную поездку.")
        return redirect("rides:ride_status", pk=ride.pk)

    if ride.rating is not None:
        messages.error(request, "Эта поездка уже оценена.")
        return redirect("rides:ride_status", pk=ride.pk)

    form = DriverReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.ride = ride
        review.save()
        ride.rating = review.rating
        ride.save(update_fields=["rating"])
        messages.success(request, "Спасибо за оценку поездки.")
    else:
        messages.error(request, "Не удалось сохранить оценку.")
    return redirect("rides:ride_status", pk=ride.pk)


@login_required
@require_POST
def complete_demo_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk, user=request.user)

    if ride.status == "cancelled":
        return JsonResponse({"ok": False, "status": ride.status}, status=400)

    if ride.status != "completed":
        ride.status = "completed"
        ride.save(update_fields=["status"])

    return JsonResponse({"ok": True, "status": ride.status})


@login_required
def ride_history(request):
    rides = Ride.objects.filter(user=request.user).select_related("tariff").order_by("-created_at")
    return render(request, "rides/history.html", {"rides": rides})
