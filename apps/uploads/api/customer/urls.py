from django.urls import path

from apps.uploads.api.customer.views import UploadCompleteView, UploadInitiateView

urlpatterns = [
    path(
        "initiate",
        UploadInitiateView.as_view(),
        name="upload-initiate",
    ),
    path(
        "<uuid:upload_id>/complete",
        UploadCompleteView.as_view(),
        name="upload-complete",
    ),
]
