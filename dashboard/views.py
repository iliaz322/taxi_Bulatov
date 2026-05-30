from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.views.generic import TemplateView

from catalog.models import Vehicle
from orders.models import Order


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in {"dispatcher", "admin"}


class DashboardHomeView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "")
        orders = Order.objects.select_related("client", "tariff", "vehicle")
        if query:
            orders = orders.filter(Q(phone__icontains=query) | Q(client__full_name__icontains=query))

        context["query"] = query
        context["new_orders"] = orders.filter(status=Order.Status.NEW)[:10]
        context["active_orders"] = orders.filter(status__in=[Order.Status.CONFIRMED, Order.Status.IN_PROGRESS])[:10]
        context["completed_orders"] = orders.filter(status=Order.Status.COMPLETED)[:10]
        context["available_vehicles"] = Vehicle.objects.filter(status=Vehicle.Status.AVAILABLE)[:10]
        return context
