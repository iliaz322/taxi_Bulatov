from django.core.validators import MinValueValidator
from django.db import models


class Tariff(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    price_per_km = models.DecimalField(
        "Цена за км",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    minimum_price = models.DecimalField(
        "Минимальная стоимость",
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ["minimum_price", "name"]
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Свободен"
        BUSY = "busy", "Занят"
        MAINTENANCE = "maintenance", "На обслуживании"

    license_plate = models.CharField("Госномер", max_length=20, unique=True)
    brand = models.CharField("Марка", max_length=80)
    model = models.CharField("Модель", max_length=80)
    color = models.CharField("Цвет", max_length=40, blank=True)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )

    class Meta:
        ordering = ["license_plate"]
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"

    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"
