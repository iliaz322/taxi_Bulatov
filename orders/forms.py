from datetime import timedelta
from decimal import Decimal

from django import forms
from django.utils import timezone

from catalog.models import Tariff
from orders.models import Order


class OrderForm(forms.ModelForm):
    class RideTiming:
        NOW = "now"
        SCHEDULED = "scheduled"
        CHOICES = (
            (NOW, "Как можно скорее"),
            (SCHEDULED, "К определенному времени"),
        )

    ride_timing = forms.ChoiceField(
        label="Когда подать машину",
        choices=RideTiming.CHOICES,
        initial=RideTiming.NOW,
        widget=forms.RadioSelect,
    )
    estimated_distance_km = forms.DecimalField(
        label="Расстояние, км",
        min_value=Decimal("0.1"),
        decimal_places=1,
        max_digits=6,
        initial=Decimal("5.0"),
    )

    class Meta:
        model = Order
        fields = [
            "pickup_address",
            "dropoff_address",
            "pickup_time",
            "phone",
            "tariff",
            "estimated_distance_km",
            "comment",
        ]
        widgets = {
            "pickup_address": forms.TextInput(attrs={"placeholder": "Откуда вас забрать"}),
            "dropoff_address": forms.TextInput(attrs={"placeholder": "Куда поедем"}),
            "pickup_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "phone": forms.TextInput(attrs={"placeholder": "+79991234567"}),
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "Комментарий водителю"}),
        }

    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop("client", None)
        super().__init__(*args, **kwargs)
        self.fields["pickup_time"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["tariff"].queryset = Tariff.objects.filter(is_active=True)
        self.fields["pickup_time"].required = False

        if self.client and getattr(self.client, "phone", "") and not self.initial.get("phone"):
            self.initial["phone"] = self.client.phone

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

        self.fields["pickup_address"].widget.attrs["autocomplete"] = "street-address"
        self.fields["dropoff_address"].widget.attrs["autocomplete"] = "street-address"
        self.fields["phone"].widget.attrs["autocomplete"] = "tel"

    def clean_pickup_time(self):
        pickup_time = self.cleaned_data["pickup_time"]
        ride_timing = self.cleaned_data.get("ride_timing")
        if ride_timing == self.RideTiming.NOW:
            return pickup_time
        if not pickup_time:
            raise forms.ValidationError("Укажите время подачи.")
        if pickup_time < timezone.now():
            raise forms.ValidationError("Время подачи не может быть в прошлом.")
        return pickup_time

    def clean(self):
        cleaned_data = super().clean()
        pickup_address = cleaned_data.get("pickup_address")
        dropoff_address = cleaned_data.get("dropoff_address")
        if pickup_address and dropoff_address and pickup_address == dropoff_address:
            self.add_error("dropoff_address", "Адрес назначения должен отличаться от адреса подачи.")

        if cleaned_data.get("ride_timing") == self.RideTiming.NOW:
            cleaned_data["pickup_time"] = timezone.now() + timedelta(minutes=10)
        return cleaned_data

    def save(self, commit=True, client=None):
        order = super().save(commit=False)
        if client is not None:
            order.client = client
        order.calculate_estimated_price()
        if commit:
            order.save()
        return order
