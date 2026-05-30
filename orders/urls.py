from django.urls import path

from orders.views import OrderCreateView, OrderDetailView, OrderHistoryView

app_name = "orders"

urlpatterns = [
    path("create/", OrderCreateView.as_view(), name="create"),
    path("history/", OrderHistoryView.as_view(), name="history"),
    path("<int:pk>/", OrderDetailView.as_view(), name="detail"),
]
