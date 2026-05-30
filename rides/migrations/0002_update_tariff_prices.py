from django.db import migrations


def update_tariffs(apps, schema_editor):
    Tariff = apps.get_model("rides", "Tariff")

    tariff_updates = {
        "Эконом": {"price_per_km": "24.00", "min_price": "289.00"},
        "Комфорт": {"price_per_km": "34.00", "min_price": "429.00"},
        "Бизнес": {"price_per_km": "55.00", "min_price": "690.00"},
    }

    for tariff in Tariff.objects.all():
        values = tariff_updates.get(tariff.name)
        if not values:
            continue

        tariff.price_per_km = values["price_per_km"]
        tariff.min_price = values["min_price"]
        tariff.save(update_fields=["price_per_km", "min_price"])


def rollback_tariffs(apps, schema_editor):
    Tariff = apps.get_model("rides", "Tariff")

    tariff_updates = {
        "Эконом": {"price_per_km": "15.00", "min_price": "150.00"},
        "Комфорт": {"price_per_km": "22.00", "min_price": "220.00"},
        "Бизнес": {"price_per_km": "40.00", "min_price": "400.00"},
    }

    for tariff in Tariff.objects.all():
        values = tariff_updates.get(tariff.name)
        if not values:
            continue

        tariff.price_per_km = values["price_per_km"]
        tariff.min_price = values["min_price"]
        tariff.save(update_fields=["price_per_km", "min_price"])


class Migration(migrations.Migration):
    dependencies = [
        ("rides", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(update_tariffs, rollback_tariffs),
    ]
