from django.db import migrations, models


def set_existing_payment_methods(apps, schema_editor):
    ride_model = apps.get_model("rides", "Ride")
    ride_model.objects.exclude(card_last4="").update(payment_method="card")
    ride_model.objects.filter(payment_status="authorized").update(payment_method="card")


class Migration(migrations.Migration):
    dependencies = [
        ("rides", "0005_add_authorized_payment_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="ride",
            name="payment_method",
            field=models.CharField(
                choices=[("cash", "Наличными"), ("card", "Картой")],
                default="cash",
                max_length=10,
                verbose_name="Способ оплаты",
            ),
        ),
        migrations.RunPython(set_existing_payment_methods, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="ride",
            name="payment_status",
            field=models.CharField(
                choices=[
                    ("unpaid", "Не оплачено"),
                    ("cash_pending", "Оплата наличными"),
                    ("authorized", "Карта привязана"),
                    ("paid", "Оплачено"),
                ],
                default="unpaid",
                max_length=20,
                verbose_name="Статус оплаты",
            ),
        ),
    ]
