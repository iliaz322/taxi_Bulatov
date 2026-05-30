from django.views.generic import TemplateView

from catalog.models import Tariff


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tariffs"] = Tariff.objects.filter(is_active=True)[:3]
        return context
