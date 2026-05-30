from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class CustomUser(AbstractUser):
    # Телефон используется как дополнительный контакт и выводится в админке.
    phone = models.CharField(
        "Телефон",
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\+?\d{10,15}$",
                message="Введите телефон в формате +79991234567.",
            )
        ],
    )
    avatar = models.ImageField("Аватар", upload_to="avatars/", blank=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.get_full_name() or self.username
