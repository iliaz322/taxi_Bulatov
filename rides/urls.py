from django.urls import path

from rides import views


app_name = "rides"

urlpatterns = [
    path("manifest.webmanifest", views.pwa_manifest, name="manifest"),
    path("service-worker.js", views.service_worker, name="service_worker"),
    path("offline/", views.offline_page, name="offline"),
    path("", views.index, name="index"),
    path("order/", views.order_ride, name="order"),
    path("ride/<int:pk>/", views.ride_status, name="ride_status"),
    path("ride/<int:pk>/sync-demo/", views.sync_demo_tracking, name="sync_demo_tracking"),
    path("ride/<int:pk>/complete-demo/", views.complete_demo_ride, name="complete_demo_ride"),
    path("ride/<int:pk>/pay/", views.pay_ride, name="pay_ride"),
    path("ride/<int:pk>/support/", views.support_chat, name="support_chat"),
    path("ride/<int:pk>/rate/", views.rate_ride, name="rate_ride"),
    path("history/", views.ride_history, name="history"),
]
