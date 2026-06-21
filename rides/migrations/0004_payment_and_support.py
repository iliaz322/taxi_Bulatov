from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("rides", "0003_lower_tariff_prices"),
    ]

    operations = [
        migrations.AddField(
            model_name="ride",
            name="card_last4",
            field=models.CharField(blank=True, max_length=4, verbose_name="Последние 4 цифры карты"),
        ),
        migrations.AddField(
            model_name="ride",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Оплачено"),
        ),
        migrations.AddField(
            model_name="ride",
            name="payment_status",
            field=models.CharField(
                choices=[("unpaid", "Не оплачено"), ("paid", "Оплачено")],
                default="unpaid",
                max_length=20,
                verbose_name="Статус оплаты",
            ),
        ),
        migrations.CreateModel(
            name="SupportMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sender", models.CharField(choices=[("client", "Клиент"), ("dispatcher", "Диспетчер")], max_length=20, verbose_name="Отправитель")),
                ("text", models.TextField(verbose_name="Текст сообщения")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                (
                    "ride",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="support_messages",
                        to="rides.ride",
                        verbose_name="Поездка",
                    ),
                ),
            ],
            options={
                "verbose_name": "Сообщение поддержки",
                "verbose_name_plural": "Сообщения поддержки",
                "ordering": ["created_at", "id"],
            },
        ),
    ]
