from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from catalog.models import Tariff, Vehicle


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        CONFIRMED = "confirmed", "Подтвержден"
        IN_PROGRESS = "in_progress", "В пути"
        COMPLETED = "completed", "Завершен"
        CANCELLED = "cancelled", "Отменен"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Клиент",
        related_name="orders",
        on_delete=models.CASCADE,
    )
    pickup_address = models.CharField("Адрес подачи", max_length=255)
    dropoff_address = models.CharField("Адрес назначения", max_length=255)
    pickup_time = models.DateTimeField("Время подачи")
    phone = models.CharField(
        "Телефон",
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^\+?\d{10,15}$",
                message="Введите телефон в формате +79991234567.",
            )
        ],
    )
    tariff = models.ForeignKey(
        Tariff,
        verbose_name="Тариф",
        related_name="orders",
        on_delete=models.PROTECT,
    )
    vehicle = models.ForeignKey(
        Vehicle,
        verbose_name="Автомобиль",
        related_name="orders",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    comment = models.TextField("Комментарий", blank=True)
    estimated_distance_km = models.DecimalField(
        "Расстояние, км",
        max_digits=6,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(0)],
    )
    estimated_price = models.DecimalField(
        "Ориентировочная стоимость",
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлен", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.pk} — {self.pickup_address}"

    def calculate_estimated_price(self):
        distance_total = self.tariff.price_per_km * self.estimated_distance_km
        self.estimated_price = max(distance_total, self.tariff.minimum_price)
        return self.estimated_price


class OrderStatus(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        related_name="status_history",
        on_delete=models.CASCADE,
    )
    status = models.CharField("Статус", max_length=20, choices=Order.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Изменил",
        related_name="status_changes",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    note = models.CharField("Комментарий", max_length=255, blank=True)
    changed_at = models.DateTimeField("Изменен", auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "История статуса"
        verbose_name_plural = "История статусов"

    def __str__(self):
        return f"{self.order_id}: {self.get_status_display()}"
