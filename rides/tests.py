from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rides.models import Ride, Tariff
from rides.utils import MOCK_DRIVERS_BY_TARIFF


class RideOrderTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="rider",
            password="StrongPass123",
            phone="+79990001124",
        )
        self.tariff = Tariff.objects.create(
            name="Эконом",
            price_per_km=Decimal("21.00"),
            min_price=Decimal("249.00"),
            description="Базовый тариф",
        )

    def test_authenticated_user_can_create_ride(self):
        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(
            reverse("rides:order"),
            {
                "from_address": "ул. Пушкина, 10",
                "to_address": "пр. Мира, 15",
                "tariff": self.tariff.pk,
                "distance_km": "12.0",
                "comment": "Буду у подъезда",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        ride = Ride.objects.get()
        self.assertEqual(ride.user, self.user)
        self.assertEqual(ride.price, Decimal("481.95"))

    def test_demo_tracking_completion_marks_ride_completed(self):
        ride = Ride.objects.create(
            user=self.user,
            tariff=self.tariff,
            from_address="ул. Пушкина, 10",
            to_address="пр. Мира, 15",
            distance_km=12,
            price=Decimal("481.95"),
            status="searching",
            driver_name="Алексей К.",
            driver_car="Toyota Camry",
            driver_plate="А123БВ 77",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(reverse("rides:complete_demo_ride", kwargs={"pk": ride.pk}))

        self.assertEqual(response.status_code, 200)
        ride.refresh_from_db()
        self.assertEqual(ride.status, "completed")

    def test_short_business_ride_is_above_base_minimum(self):
        business = Tariff.objects.create(
            name="Бизнес",
            price_per_km=Decimal("48.00"),
            min_price=Decimal("590.00"),
            description="Премиальный тариф",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(
            reverse("rides:order"),
            {
                "from_address": "ул. Пушкина, 10",
                "to_address": "пр. Мира, 15",
                "tariff": business.pk,
                "distance_km": "5.5",
                "comment": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        ride = Ride.objects.order_by("-id").first()
        self.assertEqual(ride.price, Decimal("758.00"))
        self.assertIn(
            ride.driver_car,
            [driver["car"] for driver in MOCK_DRIVERS_BY_TARIFF["Бизнес"]],
        )

    def test_index_shows_tariff_car_options(self):
        comfort = Tariff.objects.create(
            name="Комфорт",
            price_per_km=Decimal("30.00"),
            min_price=Decimal("379.00"),
            description="Комфортный тариф",
        )

        response = self.client.get(reverse("rides:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, comfort.name)
        self.assertContains(response, "Какие машины могут приехать")
        self.assertContains(response, "Toyota Camry")
