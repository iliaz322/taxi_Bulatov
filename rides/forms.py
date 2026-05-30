from decimal import Decimal

from django import forms

from rides.models import DriverReview, Ride, Tariff


class RideOrderForm(forms.ModelForm):
    # Отдельное поле расстояния позволяет показать расчет даже без карт.
    distance_km = forms.DecimalField(
        label="Расстояние, км",
        min_value=Decimal("0.5"),
        decimal_places=1,
        max_digits=6,
        initial=Decimal("5.0"),
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
