from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rides", "0004_payment_and_support"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ride",
            name="payment_status",
            field=models.CharField(
                choices=[
                    ("unpaid", "Не оплачено"),
                    ("authorized", "Карта привязана"),
                    ("paid", "Оплачено"),
                ],
                default="unpaid",
                max_length=20,
                verbose_name="Статус оплаты",
            ),
        ),
    ]
