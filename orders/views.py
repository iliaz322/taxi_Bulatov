from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from orders.forms import OrderForm
from orders.models import Order, OrderStatus


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = "orders/order_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["client"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tariffs"] = list(self.get_form().fields["tariff"].queryset)
        return context

    def form_valid(self, form):
        self.object = form.save(client=self.request.user)
        OrderStatus.objects.create(
            order=self.object,
            status=self.object.status,
            changed_by=self.request.user,
            note="Заказ создан клиентом",
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("orders:detail", kwargs={"pk": self.object.pk})


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"

    def get_queryset(self):
        queryset = Order.objects.select_related("tariff", "vehicle", "client")
        if self.request.user.role in {"dispatcher", "admin"}:
            return queryset
        return queryset.filter(client=self.request.user)


class OrderHistoryView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "orders/order_history.html"
    paginate_by = 10

    def get_queryset(self):
        return (
            Order.objects.filter(client=self.request.user)
            .select_related("tariff", "vehicle")
            .order_by("-created_at")
        )
