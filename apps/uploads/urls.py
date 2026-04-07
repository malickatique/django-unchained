from django.urls import path, include

urlpatterns = [
    path(
        "customer/",
        include("apps.uploads.api.customer.urls"),
    ),
]
