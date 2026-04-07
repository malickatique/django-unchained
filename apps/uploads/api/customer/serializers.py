from rest_framework import serializers

from apps.uploads.models import Upload


class UploadInitiateSerializer(serializers.Serializer):
    """Input for POST /uploads/initiate — client declares what it will upload."""
    filename = serializers.CharField(max_length=255)
    content_type = serializers.CharField(max_length=100)
    category = serializers.CharField(max_length=30)


class UploadInitiateResponseSerializer(serializers.ModelSerializer):
    """
    Response after initiate. Returns the upload_id and a local upload URL.

    When S3 is added, this will include upload_url, method, and headers
    for presigned upload. For local storage, the client POSTs the file
    to the complete endpoint.
    """
    upload_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Upload
        fields = [
            "upload_id",
            "status",
            "category",
            "content_type",
            "original_filename",
            "created_at",
        ]
        read_only_fields = fields


class UploadCompleteResponseSerializer(serializers.ModelSerializer):
    """Response after upload completion."""
    upload_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Upload
        fields = [
            "upload_id",
            "status",
            "original_filename",
            "content_type",
            "category",
            "size_bytes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
