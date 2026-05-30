from django.urls import path

from catalog.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
]
