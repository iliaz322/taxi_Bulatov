import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.http import require_POST

from rides.forms import DriverReviewForm, RideOrderForm, RidePaymentForm, SupportMessageForm
from rides.models import DriverReview, Ride, SupportMessage, Tariff
from rides.utils import assign_driver, build_dispatcher_reply, calculate_ride_price


def build_tracking_payload(ride):
    return {
        "rideId": ride.pk,
        "status": ride.status,
        "fromAddress": ride.from_address,
        "toAddress": ride.to_address,
        "driverName": ride.driver_name or "Водитель",
        "completeUrl": reverse("rides:complete_demo_ride", kwargs={"pk": ride.pk}),
        "syncUrl": reverse("rides:sync_demo_tracking", kwargs={"pk": ride.pk}),
        "carIconUrl": static("img/car-marker.svg"),
    }


def pwa_manifest(request):
    manifest = {
        "id": "/?source=pwa",
        "name": "TaxiGo",
        "short_name": "TaxiGo",
        "description": "Сервис заказа такси с картой, трекингом поездки и историей заказов.",
        "start_url": f"{reverse('rides:index')}?source=pwa",
        "scope": "/",
        "display": "standalone",
        "display_override": ["window-controls-overlay", "standalone", "minimal-ui", "browser"],
        "background_color": "#ffffff",
        "theme_color": "#1c1c1e",
        "lang": "ru",
        "orientation": "portrait-primary",
        "categories": ["travel", "navigation", "maps", "business"],
        "prefer_related_applications": False,
        "icons": [
            {
                "src": static("img/pwa/icon-192.png"),
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": static("img/pwa/icon-512.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": static("img/pwa/icon-maskable-512.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
        "shortcuts": [
            {
                "name": "Заказать поездку",
                "short_name": "Заказать",
                "description": "Быстрый переход к оформлению заказа.",
                "url": f"{reverse('rides:order')}?source=pwa-shortcut",
                "icons": [{"src": static("img/pwa/icon-192.png"), "sizes": "192x192", "type": "image/png"}],
            },
            {
                "name": "История поездок",
                "short_name": "История",
                "description": "Открыть последние поездки пользователя.",
                "url": f"{reverse('rides:history')}?source=pwa-shortcut",
                "icons": [{"src": static("img/pwa/icon-192.png"), "sizes": "192x192", "type": "image/png"}],
            },
            {
                "name": "Профиль",
                "short_name": "Профиль",
                "description": "Открыть личный кабинет TaxiGo.",
                "url": f"{reverse('users:profile')}?source=pwa-shortcut",
                "icons": [{"src": static("img/pwa/icon-192.png"), "sizes": "192x192", "type": "image/png"}],
            },
        ],
    }
    return JsonResponse(manifest, content_type="application/manifest+json")


def service_worker(request):
    payload = {
        "cache_name": "taxigo-shell-v2",
        "runtime_cache": "taxigo-runtime-v2",
        "offline_url": reverse("rides:offline"),
        "home_url": reverse("rides:index"),
        "login_url": reverse("users:login"),
        "register_url": reverse("users:register"),
        "manifest_url": reverse("rides:manifest"),
        "style_url": static("css/style.css"),
        "script_url": static("js/main.js"),
        "logo_url": static("img/taxigo-mark.svg"),
        "icon_192_url": static("img/pwa/icon-192.png"),
        "icon_512_url": static("img/pwa/icon-512.png"),
        "apple_icon_url": static("img/pwa/apple-touch-icon-180.png"),
    }
    response = HttpResponse(
        (
            "const CACHE_NAME = {cache};\n"
            "const RUNTIME_CACHE = {runtime_cache};\n"
            "const OFFLINE_URL = {offline};\n"
            "const APP_SHELL = [\n"
            "  {home},\n"
            "  {login},\n"
            "  {register},\n"
            "  {manifest},\n"
            "  {style},\n"
            "  {script},\n"
            "  {logo},\n"
            "  {icon192},\n"
            "  {icon512},\n"
            "  {appleicon},\n"
            "  OFFLINE_URL,\n"
            "];\n\n"
            "self.addEventListener(\"install\", (event) => {{\n"
            "  event.waitUntil(\n"
            "    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())\n"
            "  );\n"
            "}});\n\n"
            "self.addEventListener(\"activate\", (event) => {{\n"
            "  event.waitUntil(\n"
            "    caches.keys().then((keys) =>\n"
            "      Promise.all(\n"
            "        keys.map((key) => {{\n"
            "          if (![CACHE_NAME, RUNTIME_CACHE].includes(key)) {{\n"
            "            return caches.delete(key);\n"
            "          }}\n"
            "          return Promise.resolve();\n"
            "        }})\n"
            "      )\n"
            "    ).then(async () => {{\n"
            "      if (self.registration.navigationPreload) {{\n"
            "        await self.registration.navigationPreload.enable();\n"
            "      }}\n"
            "      return self.clients.claim();\n"
            "    }})\n"
            "  );\n"
            "}});\n\n"
            "self.addEventListener(\"fetch\", (event) => {{\n"
            "  if (event.request.method !== \"GET\") {{\n"
            "    return;\n"
            "  }}\n\n"
            "  const requestUrl = new URL(event.request.url);\n"
            "  const isSameOrigin = requestUrl.origin === self.location.origin;\n"
            "  const acceptsHtml = event.request.headers.get(\"accept\")?.includes(\"text/html\");\n\n"
            "  if (!isSameOrigin) {{\n"
            "    return;\n"
            "  }}\n\n"
            "  const isStaticAsset = [\"style\", \"script\", \"image\", \"font\"].includes(event.request.destination);\n\n"
            "  if (acceptsHtml) {{\n"
            "    event.respondWith(\n"
            "      (async () => {{\n"
            "        try {{\n"
            "          const preloadResponse = await event.preloadResponse;\n"
            "          if (preloadResponse) {{\n"
            "            const preloadClone = preloadResponse.clone();\n"
            "            caches.open(RUNTIME_CACHE).then((cache) => cache.put(event.request, preloadClone));\n"
            "            return preloadResponse;\n"
            "          }}\n"
            "          const response = await fetch(event.request);\n"
            "          const responseClone = response.clone();\n"
            "          caches.open(RUNTIME_CACHE).then((cache) => cache.put(event.request, responseClone));\n"
            "          return response;\n"
            "        }} catch (error) {{\n"
            "          const cachedPage = await caches.match(event.request);\n"
            "          return cachedPage || caches.match(OFFLINE_URL);\n"
            "        }}\n"
            "      }})()\n"
            "    );\n"
            "    return;\n"
            "  }}\n\n"
            "  if (isStaticAsset) {{\n"
            "    event.respondWith(\n"
            "      caches.match(event.request).then((cachedResponse) => {{\n"
            "        const fetchPromise = fetch(event.request)\n"
            "          .then((response) => {{\n"
            "            if (response && response.status === 200 && response.type === \"basic\") {{\n"
            "              const responseClone = response.clone();\n"
            "              caches.open(RUNTIME_CACHE).then((cache) => cache.put(event.request, responseClone));\n"
            "            }}\n"
            "            return response;\n"
            "          }})\n"
            "          .catch(() => cachedResponse || caches.match({icon192}));\n"
            "        return cachedResponse || fetchPromise;\n"
            "      }})\n"
            "    );\n"
            "    return;\n"
            "  }}\n\n"
            "  event.respondWith(\n"
            "    caches.match(event.request).then((cachedResponse) => {{\n"
            "      if (cachedResponse) {{\n"
            "        return cachedResponse;\n"
            "      }}\n\n"
            "      return fetch(event.request)\n"
            "        .then((response) => {{\n"
            "          if (!response || response.status !== 200 || response.type !== \"basic\") {{\n"
            "            return response;\n"
            "          }}\n"
            "          const responseClone = response.clone();\n"
            "          caches.open(RUNTIME_CACHE).then((cache) => cache.put(event.request, responseClone));\n"
            "          return response;\n"
            "        }})\n"
            "        .catch(() => caches.match({logo}));\n"
            "    }})\n"
            "  );\n"
            "}});\n"
        ).format(
            cache=json.dumps(payload["cache_name"]),
            runtime_cache=json.dumps(payload["runtime_cache"]),
            offline=json.dumps(payload["offline_url"]),
            home=json.dumps(payload["home_url"]),
            login=json.dumps(payload["login_url"]),
            register=json.dumps(payload["register_url"]),
            manifest=json.dumps(payload["manifest_url"]),
            style=json.dumps(payload["style_url"]),
            script=json.dumps(payload["script_url"]),
            logo=json.dumps(payload["logo_url"]),
            icon192=json.dumps(payload["icon_192_url"]),
            icon512=json.dumps(payload["icon_512_url"]),
            appleicon=json.dumps(payload["apple_icon_url"]),
        ),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


def offline_page(request):
    return render(request, "pwa/offline.html")


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
            ride.payment_method = form.cleaned_data["payment_method"]
            if ride.payment_method == "card":
                ride.payment_status = "authorized"
                ride.card_last4 = form.cleaned_data["card_number"][-4:]
            else:
                ride.payment_status = "cash_pending"
                ride.card_last4 = ""
            ride.save()

            payment_message = "Карта привязана, списание будет после поездки." if ride.payment_method == "card" else "Оплата наличными после поездки."
            messages.success(request, f"Заказ создан. {payment_message}")
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
    payment_form = RidePaymentForm()
    support_form = SupportMessageForm()
    tracking_payload = build_tracking_payload(ride)
    return render(
        request,
        "rides/ride_status.html",
        {
            "ride": ride,
            "review_form": review_form,
            "payment_form": payment_form,
            "support_form": support_form,
            "support_messages": ride.support_messages.all(),
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
def sync_demo_tracking(request, pk):
    ride = get_object_or_404(Ride, pk=pk, user=request.user)

    if ride.status in {"completed", "cancelled"}:
        return JsonResponse({"ok": True, "status": ride.status})

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}

    next_status = payload.get("status")
    if next_status != "active":
        return JsonResponse({"ok": False, "error": "Неподдерживаемый этап трекинга."}, status=400)

    if ride.payment_status == "unpaid":
        return JsonResponse({"ok": False, "error": "Сначала оплатите или привяжите карту."}, status=409)

    if ride.status != "active":
        ride.status = "active"
        ride.save(update_fields=["status"])

    return JsonResponse({"ok": True, "status": ride.status})


@login_required
@require_POST
def complete_demo_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk, user=request.user)

    if ride.status == "cancelled":
        return JsonResponse({"ok": False, "status": ride.status}, status=400)

    if ride.payment_status == "unpaid":
        return JsonResponse(
            {"ok": False, "error": "Сначала привяжите карту к поездке."},
            status=409,
        )

    if ride.status != "completed":
        ride.status = "completed"
        update_fields = ["status"]
        if ride.payment_status in {"authorized", "cash_pending"}:
            ride.payment_status = "paid"
            ride.paid_at = timezone.now()
            update_fields.extend(["payment_status", "paid_at"])
        ride.save(update_fields=update_fields)

    return JsonResponse(
        {
            "ok": True,
            "status": ride.status,
            "payment_status": ride.payment_status,
        }
    )


@login_required
@require_POST
def pay_ride(request, pk):
    ride = get_object_or_404(Ride, pk=pk, user=request.user)
    if ride.payment_status in {"authorized", "paid"}:
        messages.success(
            request,
            "Карта уже привязана к заказу." if ride.payment_status == "authorized" else "Поездка уже оплачена.",
        )
        return redirect("rides:ride_status", pk=ride.pk)

    form = RidePaymentForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Не удалось провести демонстрационную оплату. Проверьте форму.")
        review_form = DriverReviewForm()
        support_form = SupportMessageForm()
        tracking_payload = build_tracking_payload(ride)
        return render(
            request,
            "rides/ride_status.html",
            {
                "ride": ride,
                "review_form": review_form,
                "payment_form": form,
                "support_form": support_form,
                "support_messages": ride.support_messages.all(),
                "yandex_maps_api_key": settings.YANDEX_MAPS_API_KEY,
                "tracking_payload": tracking_payload,
            },
        )

    ride.payment_status = "paid" if ride.status == "completed" else "authorized"
    ride.payment_method = "card"
    ride.card_last4 = form.cleaned_data["card_number"][-4:]
    ride.paid_at = timezone.now() if ride.payment_status == "paid" else None
    ride.save(update_fields=["payment_method", "payment_status", "card_last4", "paid_at"])
    if ride.payment_status == "paid":
        messages.success(request, "Карта привязана, демонстрационная оплата завершена.")
    else:
        messages.success(request, "Карта привязана. Списание произойдёт автоматически после завершения поездки.")
    return redirect("rides:ride_status", pk=ride.pk)


@login_required
@require_POST
def support_chat(request, pk):
    ride = get_object_or_404(Ride, pk=pk, user=request.user)
    form = SupportMessageForm(request.POST)
    if form.is_valid():
        client_message = form.save(commit=False)
        client_message.ride = ride
        client_message.sender = "client"
        client_message.save()

        SupportMessage.objects.create(
            ride=ride,
            sender="dispatcher",
            text=build_dispatcher_reply(client_message.text),
        )
        messages.success(request, "Сообщение отправлено в поддержку.")
    else:
        messages.error(request, "Не удалось отправить сообщение. Проверьте текст обращения.")
    return redirect("rides:ride_status", pk=ride.pk)


@login_required
def ride_history(request):
    rides = Ride.objects.filter(user=request.user).select_related("tariff").order_by("-created_at")
    return render(request, "rides/history.html", {"rides": rides})
