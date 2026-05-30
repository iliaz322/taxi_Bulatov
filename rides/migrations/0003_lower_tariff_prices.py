from django.db import migrations


def lower_tariff_prices(apps, schema_editor):
    Tariff = apps.get_model("rides", "Tariff")

    updates = {
        "Эконом": {"min_price": "249.00", "price_per_km": "21.00"},
        "Комфорт": {"min_price": "379.00", "price_per_km": "30.00"},
        "Бизнес": {"min_price": "590.00", "price_per_km": "48.00"},
    }

    for tariff_name, values in updates.items():
        Tariff.objects.filter(name=tariff_name).update(**values)


class Migration(migrations.Migration):
    dependencies = [
        ("rides", "0002_update_tariff_prices"),
    ]

    operations = [
        migrations.RunPython(lower_tariff_prices, migrations.RunPython.noop),
    ]
