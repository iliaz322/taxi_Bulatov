from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rides.forms import RideOrderForm
from rides.models import Ride, SupportMessage, Tariff
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
        self.assertEqual(ride.payment_method, "cash")
        self.assertEqual(ride.payment_status, "cash_pending")

    def test_user_can_create_ride_with_valid_card(self):
        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(
            reverse("rides:order"),
            {
                "from_address": "ул. Пушкина, 10",
                "to_address": "пр. Мира, 15",
                "tariff": self.tariff.pk,
                "distance_km": "12.0",
                "comment": "",
                "payment_method": "card",
                "card_number": "4111 1111 1111 1111",
                "card_holder": "IVAN IVANOV",
                "expiry_month": "12",
                "expiry_year": "30",
                "cvv": "123",
            },
        )

        self.assertEqual(response.status_code, 302)
        ride = Ride.objects.get()
        self.assertEqual(ride.payment_method, "card")
        self.assertEqual(ride.payment_status, "authorized")
        self.assertEqual(ride.card_last4, "1111")

    def test_user_can_create_ride_with_demo_card_number(self):
        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(
            reverse("rides:order"),
            {
                "from_address": "ул. Пушкина, 10",
                "to_address": "пр. Мира, 15",
                "tariff": self.tariff.pk,
                "distance_km": "12.0",
                "comment": "",
                "payment_method": "card",
                "card_number": "4242 4242 4242 4242",
                "card_holder": "IVAN IVANOV",
                "expiry_month": "12",
                "expiry_year": "30",
                "cvv": "123",
            },
        )

        self.assertEqual(response.status_code, 302)
        ride = Ride.objects.order_by("-id").first()
        self.assertEqual(ride.payment_status, "authorized")
        self.assertEqual(ride.card_last4, "4242")

    def test_card_order_rejects_18_digit_number(self):
        form = RideOrderForm(
            data={
                "from_address": "ул. Пушкина, 10",
                "to_address": "пр. Мира, 15",
                "tariff": self.tariff.pk,
                "distance_km": "12.0",
                "comment": "",
                "payment_method": "card",
                "card_number": "411111111111111111",
                "card_holder": "IVAN IVANOV",
                "expiry_month": "12",
                "expiry_year": "30",
                "cvv": "123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("ровно 16 цифр", form.errors["card_number"][0])

    def test_card_order_rejects_invalid_checksum(self):
        form = RideOrderForm(
            data={
                "from_address": "ул. Пушкина, 10",
                "to_address": "пр. Мира, 15",
                "tariff": self.tariff.pk,
                "distance_km": "12.0",
                "comment": "",
                "payment_method": "card",
                "card_number": "4111 1111 1111 1112",
                "card_holder": "IVAN IVANOV",
                "expiry_month": "12",
                "expiry_year": "30",
                "cvv": "123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Для демо используйте 4111 1111 1111 1111", form.errors["card_number"][0])

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
            payment_status="authorized",
            card_last4="1111",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(reverse("rides:complete_demo_ride", kwargs={"pk": ride.pk}))

        self.assertEqual(response.status_code, 200)
        ride.refresh_from_db()
        self.assertEqual(ride.status, "completed")
        self.assertEqual(ride.payment_status, "paid")
        self.assertIsNotNone(ride.paid_at)

    def test_demo_tracking_cannot_start_without_card(self):
        ride = Ride.objects.create(
            user=self.user,
            tariff=self.tariff,
            from_address="ул. Пушкина, 10",
            to_address="пр. Мира, 15",
            distance_km=12,
            price=Decimal("481.95"),
            status="searching",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(reverse("rides:complete_demo_ride", kwargs={"pk": ride.pk}))

        self.assertEqual(response.status_code, 409)
        ride.refresh_from_db()
        self.assertEqual(ride.status, "searching")
        self.assertEqual(ride.payment_status, "unpaid")

    def test_cash_payment_is_completed_after_demo_ride(self):
        ride = Ride.objects.create(
            user=self.user,
            tariff=self.tariff,
            from_address="ул. Пушкина, 10",
            to_address="пр. Мира, 15",
            distance_km=12,
            price=Decimal("481.95"),
            status="searching",
            payment_method="cash",
            payment_status="cash_pending",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(reverse("rides:complete_demo_ride", kwargs={"pk": ride.pk}))

        self.assertEqual(response.status_code, 200)
        ride.refresh_from_db()
        self.assertEqual(ride.status, "completed")
        self.assertEqual(ride.payment_status, "paid")
        self.assertIsNotNone(ride.paid_at)

    def test_demo_tracking_sync_marks_ride_active(self):
        ride = Ride.objects.create(
            user=self.user,
            tariff=self.tariff,
            from_address="ул. Пушкина, 10",
            to_address="пр. Мира, 15",
            distance_km=12,
            price=Decimal("481.95"),
            status="searching",
            payment_status="authorized",
            card_last4="1111",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(
            reverse("rides:sync_demo_tracking", kwargs={"pk": ride.pk}),
            data='{"status":"active"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        ride.refresh_from_db()
        self.assertEqual(ride.status, "active")

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

    def test_user_can_pay_ride_in_demo_mode(self):
        ride = Ride.objects.create(
            user=self.user,
            tariff=self.tariff,
            from_address="ул. Пушкина, 10",
            to_address="пр. Мира, 15",
            distance_km=7,
            price=Decimal("354.00"),
            status="searching",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(
            reverse("rides:pay_ride", kwargs={"pk": ride.pk}),
            {
                "card_number": "4111 1111 1111 1111",
                "card_holder": "IVAN IVANOV",
                "expiry_month": "12",
                "expiry_year": "28",
                "cvv": "123",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        ride.refresh_from_db()
        self.assertEqual(ride.payment_status, "authorized")
        self.assertEqual(ride.card_last4, "1111")
        self.assertIsNone(ride.paid_at)

    def test_completed_legacy_ride_is_paid_when_card_is_added(self):
        ride = Ride.objects.create(
            user=self.user,
            tariff=self.tariff,
            from_address="ул. Пушкина, 10",
            to_address="пр. Мира, 15",
            distance_km=7,
            price=Decimal("354.00"),
            status="completed",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(
            reverse("rides:pay_ride", kwargs={"pk": ride.pk}),
            {
                "card_number": "4111 1111 1111 1111",
                "card_holder": "IVAN IVANOV",
                "expiry_month": "12",
                "expiry_year": "28",
                "cvv": "123",
            },
        )

        self.assertEqual(response.status_code, 302)
        ride.refresh_from_db()
        self.assertEqual(ride.payment_status, "paid")
        self.assertIsNotNone(ride.paid_at)

    def test_support_chat_creates_dispatcher_reply(self):
        ride = Ride.objects.create(
            user=self.user,
            tariff=self.tariff,
            from_address="ул. Пушкина, 10",
            to_address="пр. Мира, 15",
            distance_km=7,
            price=Decimal("354.00"),
            status="searching",
        )

        self.client.login(username="rider", password="StrongPass123")
        response = self.client.post(
            reverse("rides:support_chat", kwargs={"pk": ride.pk}),
            {"text": "Подскажите, когда приедет водитель?"},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SupportMessage.objects.filter(ride=ride).count(), 2)
        self.assertTrue(
            SupportMessage.objects.filter(ride=ride, sender="dispatcher").exists()
        )


class PwaRoutesTests(TestCase):
    def test_manifest_is_available(self):
        response = self.client.get(reverse("rides:manifest"))
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        self.assertEqual(payload["name"], "TaxiGo")
        self.assertEqual(payload["display"], "standalone")
        self.assertGreaterEqual(len(payload["icons"]), 3)
        self.assertGreaterEqual(len(payload["shortcuts"]), 3)
        self.assertTrue(any(icon["purpose"] == "maskable" for icon in payload["icons"]))

    def test_service_worker_is_available(self):
        response = self.client.get(reverse("rides:service_worker"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/javascript")
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertIn("CACHE_NAME", content)
        self.assertIn("RUNTIME_CACHE", content)
        self.assertIn("navigationPreload.enable", content)
