from django.urls import path

from .views import MyUsageView


urlpatterns = [
    path("me/", MyUsageView.as_view(), name="my_usage"),
]