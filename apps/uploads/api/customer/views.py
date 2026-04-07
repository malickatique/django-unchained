from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.uploads.api.customer.serializers import (
    UploadCompleteResponseSerializer,
    UploadInitiateResponseSerializer,
    UploadInitiateSerializer,
)
from apps.uploads.services import upload_service


class UploadInitiateView(APIView):
    """
    POST /api/v1/me/uploads/initiate

    Phase 1 of the two-phase upload flow.
    Client declares filename, content_type, and category.
    Server creates a PENDING Upload record and returns the upload_id.
    """
    # TODO: Replace with [IsAuthenticated] when auth is wired up.
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UploadInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload = upload_service.initiate_upload(
            user=request.user,
            filename=serializer.validated_data["filename"],
            content_type=serializer.validated_data["content_type"],
            category=serializer.validated_data["category"],
        )

        response_serializer = UploadInitiateResponseSerializer(upload)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UploadCompleteView(APIView):
    """
    POST /api/v1/me/uploads/{upload_id}/complete

    Phase 2 of the two-phase upload flow.
    Client sends the actual file as multipart form data.
    Server persists to local storage and updates the Upload record.
    """
    # TODO: Replace with [IsAuthenticated] when auth is wired up.
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def post(self, request, upload_id):
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"file": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        upload = upload_service.complete_upload(
            upload_id=upload_id,
            user=request.user,
            file_content=file_obj.read(),
        )

        response_serializer = UploadCompleteResponseSerializer(upload)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
