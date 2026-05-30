from django.urls import path

from rides import views


app_name = "rides"

urlpatterns = [
    path("", views.index, name="index"),
    path("order/", views.order_ride, name="order"),
    path("ride/<int:pk>/", views.ride_status, name="ride_status"),
    path("ride/<int:pk>/complete-demo/", views.complete_demo_ride, name="complete_demo_ride"),
    path("ride/<int:pk>/rate/", views.rate_ride, name="rate_ride"),
    path("history/", views.ride_history, name="history"),
]
