from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MaxValueValidator, MinValueValidator


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Driver",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Имя")),
                ("car", models.CharField(max_length=100, verbose_name="Автомобиль")),
                ("plate", models.CharField(max_length=20, verbose_name="Госномер")),
                ("rating", models.DecimalField(decimal_places=2, default=Decimal("4.80"), max_digits=3, verbose_name="Рейтинг")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={"verbose_name": "Водитель", "verbose_name_plural": "Водители"},
        ),
        migrations.CreateModel(
            name="Tariff",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, verbose_name="Название")),
                ("price_per_km", models.DecimalField(decimal_places=2, max_digits=8, validators=[MinValueValidator(0)], verbose_name="Цена за км")),
                ("min_price", models.DecimalField(decimal_places=2, max_digits=8, validators=[MinValueValidator(0)], verbose_name="Минимальная стоимость")),
                ("description", models.TextField(verbose_name="Описание")),
            ],
            options={"verbose_name": "Тариф", "verbose_name_plural": "Тарифы", "ordering": ["min_price", "name"]},
        ),
        migrations.CreateModel(
            name="Ride",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_address", models.CharField(max_length=255, verbose_name="Откуда")),
                ("to_address", models.CharField(max_length=255, verbose_name="Куда")),
                ("comment", models.TextField(blank=True, verbose_name="Комментарий")),
                ("distance_km", models.FloatField(blank=True, null=True, verbose_name="Расстояние, км")),
                ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name="Стоимость")),
                ("status", models.CharField(choices=[("searching", "Поиск"), ("active", "В пути"), ("completed", "Завершена"), ("cancelled", "Отменена")], default="searching", max_length=20, verbose_name="Статус")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("driver_name", models.CharField(blank=True, max_length=100, verbose_name="Водитель")),
                ("driver_car", models.CharField(blank=True, max_length=100, verbose_name="Автомобиль")),
                ("driver_plate", models.CharField(blank=True, max_length=20, verbose_name="Номер")),
                ("rating", models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Оценка")),
                ("tariff", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="rides.tariff", verbose_name="Тариф")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rides", to=settings.AUTH_USER_MODEL, verbose_name="Пользователь")),
            ],
            options={"verbose_name": "Поездка", "verbose_name_plural": "Поездки", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DriverReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Оценка")),
                ("comment", models.TextField(blank=True, verbose_name="Комментарий")),
                ("ride", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="rides.ride", verbose_name="Поездка")),
            ],
            options={"verbose_name": "Отзыв водителю", "verbose_name_plural": "Отзывы водителям"},
        ),
    ]
