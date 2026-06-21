from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Tariff(models.Model):
    # Базовые тарифы, которые выводятся на лендинге и в форме заказа.
    name = models.CharField("Название", max_length=50)
    price_per_km = models.DecimalField("Цена за км", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    min_price = models.DecimalField("Минимальная стоимость", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField("Описание")

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        ordering = ["min_price", "name"]

    def __str__(self):
        return self.name


class Driver(models.Model):
    # Модель водителя оставлена для будущего расширения проекта.
    name = models.CharField("Имя", max_length=100)
    car = models.CharField("Автомобиль", max_length=100)
    plate = models.CharField("Госномер", max_length=20)
    rating = models.DecimalField("Рейтинг", max_digits=3, decimal_places=2, default=Decimal("4.80"))
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"

    def __str__(self):
        return f"{self.name} — {self.car}"


class Ride(models.Model):
    STATUS = [
        ("searching", "Поиск"),
        ("active", "В пути"),
        ("completed", "Завершена"),
        ("cancelled", "Отменена"),
    ]
    PAYMENT_STATUS = [
        ("unpaid", "Не оплачено"),
        ("cash_pending", "Оплата наличными"),
        ("authorized", "Карта привязана"),
        ("paid", "Оплачено"),
    ]
    PAYMENT_METHOD = [
        ("cash", "Наличными"),
        ("card", "Картой"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rides", verbose_name="Пользователь")
    tariff = models.ForeignKey(Tariff, on_delete=models.SET_NULL, null=True, verbose_name="Тариф")
    from_address = models.CharField("Откуда", max_length=255)
    to_address = models.CharField("Куда", max_length=255)
    comment = models.TextField("Комментарий", blank=True)
    distance_km = models.FloatField("Расстояние, км", null=True, blank=True)
    price = models.DecimalField("Стоимость", max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS, default="searching")
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    driver_name = models.CharField("Водитель", max_length=100, blank=True)
    driver_car = models.CharField("Автомобиль", max_length=100, blank=True)
    driver_plate = models.CharField("Номер", max_length=20, blank=True)
    payment_method = models.CharField("Способ оплаты", max_length=10, choices=PAYMENT_METHOD, default="cash")
    payment_status = models.CharField("Статус оплаты", max_length=20, choices=PAYMENT_STATUS, default="unpaid")
    card_last4 = models.CharField("Последние 4 цифры карты", max_length=4, blank=True)
    paid_at = models.DateTimeField("Оплачено", null=True, blank=True)
    rating = models.PositiveSmallIntegerField("Оценка", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        verbose_name = "Поездка"
        verbose_name_plural = "Поездки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.from_address} → {self.to_address}"


class DriverReview(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, verbose_name="Поездка")
    rating = models.PositiveSmallIntegerField("Оценка", validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField("Комментарий", blank=True)

    class Meta:
        verbose_name = "Отзыв водителю"
        verbose_name_plural = "Отзывы водителям"

    def __str__(self):
        return f"Отзыв к поездке #{self.ride_id}"


class SupportMessage(models.Model):
    SENDER_CHOICES = [
        ("client", "Клиент"),
        ("dispatcher", "Диспетчер"),
    ]

    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name="support_messages", verbose_name="Поездка")
    sender = models.CharField("Отправитель", max_length=20, choices=SENDER_CHOICES)
    text = models.TextField("Текст сообщения")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение поддержки"
        verbose_name_plural = "Сообщения поддержки"
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.get_sender_display()} — поездка #{self.ride_id}"
