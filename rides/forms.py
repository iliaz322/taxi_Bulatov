from decimal import Decimal

from django import forms
from django.utils import timezone

from rides.models import DriverReview, Ride, SupportMessage, Tariff


class CardDetailsValidationMixin:
    DEMO_CARD_NUMBERS = {
        "4111111111111111",
        "4242424242424242",
        "5555555555554444",
        "2200000000000004",
    }

    def should_validate_card(self, cleaned_data):
        return True

    def clean(self):
        cleaned_data = super().clean()
        if not self.should_validate_card(cleaned_data):
            return cleaned_data

        required_fields = ("card_number", "card_holder", "expiry_month", "expiry_year", "cvv")
        for field_name in required_fields:
            if not cleaned_data.get(field_name):
                self.add_error(field_name, "Заполните это поле.")

        raw_number = cleaned_data.get("card_number", "")
        card_number = raw_number.replace(" ", "").replace("-", "")
        if card_number:
            if not card_number.isdigit() or len(card_number) != 16:
                self.add_error("card_number", "Номер карты должен содержать ровно 16 цифр.")
            elif len(set(card_number)) == 1 or not self._is_demo_card_allowed(card_number):
                self.add_error(
                    "card_number",
                    "Проверьте номер карты. Для демо используйте 4111 1111 1111 1111 или кнопку автозаполнения.",
                )
            else:
                cleaned_data["card_number"] = card_number

        card_holder = " ".join(cleaned_data.get("card_holder", "").split()).upper()
        if card_holder and len(card_holder) < 3:
            self.add_error("card_holder", "Введите имя держателя как на карте.")
        elif card_holder:
            cleaned_data["card_holder"] = card_holder

        month = cleaned_data.get("expiry_month", "")
        year = cleaned_data.get("expiry_year", "")
        if month and (not month.isdigit() or not 1 <= int(month) <= 12):
            self.add_error("expiry_month", "Месяц должен быть от 01 до 12.")
        elif month:
            cleaned_data["expiry_month"] = month.zfill(2)

        if year and (not year.isdigit() or len(year) != 2):
            self.add_error("expiry_year", "Введите две цифры года.")

        if month.isdigit() and year.isdigit() and len(year) == 2 and 1 <= int(month) <= 12:
            today = timezone.localdate()
            expiry_year = 2000 + int(year)
            if (expiry_year, int(month)) < (today.year, today.month):
                self.add_error("expiry_year", "Срок действия карты уже истёк.")
            elif expiry_year > today.year + 20:
                self.add_error("expiry_year", "Проверьте год действия карты.")

        cvv = cleaned_data.get("cvv", "")
        if cvv and (not cvv.isdigit() or len(cvv) != 3):
            self.add_error("cvv", "CVV должен содержать ровно 3 цифры.")

        return cleaned_data

    @staticmethod
    def _passes_luhn(card_number):
        checksum = 0
        parity = len(card_number) % 2
        for index, character in enumerate(card_number):
            digit = int(character)
            if index % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0

    @classmethod
    def _is_demo_card_allowed(cls, card_number):
        return card_number in cls.DEMO_CARD_NUMBERS or cls._passes_luhn(card_number)


class RideOrderForm(CardDetailsValidationMixin, forms.ModelForm):
    # Отдельное поле расстояния позволяет показать расчет даже без карт.
    distance_km = forms.DecimalField(
        label="Расстояние, км",
        min_value=Decimal("0.5"),
        decimal_places=1,
        max_digits=6,
        initial=Decimal("5.0"),
    )
    payment_method = forms.ChoiceField(
        label="Способ оплаты",
        choices=Ride.PAYMENT_METHOD,
        initial="cash",
        required=False,
        widget=forms.RadioSelect,
    )
    card_number = forms.CharField(label="Номер карты", max_length=23, required=False)
    card_holder = forms.CharField(label="Имя держателя", max_length=100, required=False)
    expiry_month = forms.CharField(label="Месяц", max_length=2, required=False)
    expiry_year = forms.CharField(label="Год", max_length=2, required=False)
    cvv = forms.CharField(
        label="CVV",
        max_length=3,
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )

    class Meta:
        model = Ride
        fields = ("from_address", "to_address", "tariff", "distance_km", "comment")
        widgets = {
            "from_address": forms.TextInput(attrs={"placeholder": "Откуда"}),
            "to_address": forms.TextInput(attrs={"placeholder": "Куда"}),
            "distance_km": forms.NumberInput(attrs={"step": "0.1", "min": "0.5"}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Комментарий для водителя"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tariff"].queryset = Tariff.objects.all()
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["distance_km"].widget.attrs["readonly"] = True
        self._configure_card_widgets()

    def _configure_card_widgets(self):
        attributes = {
            "card_number": {
                "placeholder": "0000 0000 0000 0000",
                "inputmode": "numeric",
                "autocomplete": "cc-number",
                "maxlength": "23",
                "data-card-number": "",
            },
            "card_holder": {
                "placeholder": "ИМЯ ФАМИЛИЯ",
                "autocomplete": "cc-name",
                "data-card-holder": "",
            },
            "expiry_month": {
                "placeholder": "ММ",
                "inputmode": "numeric",
                "autocomplete": "cc-exp-month",
                "maxlength": "2",
                "data-card-month": "",
            },
            "expiry_year": {
                "placeholder": "ГГ",
                "inputmode": "numeric",
                "autocomplete": "cc-exp-year",
                "maxlength": "2",
                "data-card-year": "",
            },
            "cvv": {
                "placeholder": "123",
                "inputmode": "numeric",
                "autocomplete": "cc-csc",
                "maxlength": "3",
                "data-card-cvv": "",
            },
        }
        for field_name, field_attributes in attributes.items():
            self.fields[field_name].widget.attrs.update(field_attributes)

    def should_validate_card(self, cleaned_data):
        payment_method = cleaned_data.get("payment_method") or "cash"
        cleaned_data["payment_method"] = payment_method
        return payment_method == "card"

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("from_address") == cleaned_data.get("to_address"):
            self.add_error("to_address", "Адрес назначения должен отличаться от адреса отправления.")
        return cleaned_data


class DriverReviewForm(forms.ModelForm):
    class Meta:
        model = DriverReview
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.HiddenInput(),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Расскажите, как прошла поездка"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class RidePaymentForm(CardDetailsValidationMixin, forms.Form):
    card_number = forms.CharField(label="Номер карты", max_length=23)
    card_holder = forms.CharField(label="Имя держателя", max_length=100)
    expiry_month = forms.CharField(label="Месяц", max_length=2)
    expiry_year = forms.CharField(label="Год", max_length=2)
    cvv = forms.CharField(label="CVV", max_length=3, widget=forms.PasswordInput(render_value=True))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "card_number": "0000 0000 0000 0000",
            "card_holder": "IVAN IVANOV",
            "expiry_month": "MM",
            "expiry_year": "YY",
            "cvv": "123",
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("placeholder", placeholders[name])
            field.widget.attrs.setdefault("inputmode", "numeric")
        self.fields["card_number"].widget.attrs.update({"maxlength": "23", "autocomplete": "cc-number"})
        self.fields["card_holder"].widget.attrs.update({"inputmode": "text", "autocomplete": "cc-name"})
        self.fields["expiry_month"].widget.attrs.update({"maxlength": "2", "autocomplete": "cc-exp-month"})
        self.fields["expiry_year"].widget.attrs.update({"maxlength": "2", "autocomplete": "cc-exp-year"})
        self.fields["cvv"].widget.attrs.update({"maxlength": "3", "autocomplete": "cc-csc"})


class SupportMessageForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ("text",)
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Напишите вопрос по заказу, оплате или маршруту",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
