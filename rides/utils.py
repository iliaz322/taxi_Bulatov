import random
from decimal import Decimal, ROUND_HALF_UP


MOCK_DRIVERS_BY_TARIFF = {
    "Эконом": [
        {"name": "Ирина Н.", "car": "Volkswagen Polo", "plate": "Р567СУ 77"},
        {"name": "Дмитрий П.", "car": "Skoda Octavia", "plate": "М231ТА 77"},
        {"name": "Олег В.", "car": "Geely Coolray", "plate": "Т332НЕ 77"},
    ],
    "Комфорт": [
        {"name": "Алексей К.", "car": "Toyota Camry", "plate": "А123БВ 77"},
        {"name": "Марина С.", "car": "Kia K5", "plate": "В456ОР 77"},
        {"name": "Руслан М.", "car": "Hyundai Sonata", "plate": "Е784КК 77"},
    ],
    "Бизнес": [
        {"name": "Сергей Л.", "car": "Mercedes-Benz E-Class", "plate": "Х908РА 77"},
        {"name": "Тимур Г.", "car": "BMW 5 Series", "plate": "К410МН 77"},
        {"name": "Анна В.", "car": "Audi A6", "plate": "У245СР 77"},
    ],
}

DEFAULT_DRIVERS = [
    {"name": "Алексей К.", "car": "Toyota Camry", "plate": "А123БВ 77"},
    {"name": "Ирина Н.", "car": "Volkswagen Polo", "plate": "Р567СУ 77"},
]


def assign_driver(tariff):
    # Выбираем машину из пула, который соответствует тарифу.
    driver_pool = MOCK_DRIVERS_BY_TARIFF.get(getattr(tariff, "name", ""), DEFAULT_DRIVERS)
    return random.choice(driver_pool)


def calculate_ride_price(distance_km, tariff):
    # Базовая логика такси: в цену входит подача и первые 2 км,
    # затем каждый следующий километр оплачивается отдельно.
    distance = Decimal(str(distance_km))
    included_distance = Decimal("2.0")
    paid_distance = max(distance - included_distance, Decimal("0.0"))
    subtotal = tariff.min_price + (paid_distance * tariff.price_per_km)

    multiplier = Decimal("1.00")
    if distance > Decimal("35"):
        multiplier = Decimal("1.20")
    elif distance > Decimal("20"):
        multiplier = Decimal("1.11")
    elif distance > Decimal("10"):
        multiplier = Decimal("1.05")

    return (subtotal * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
