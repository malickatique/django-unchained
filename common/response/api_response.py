"""
Thin helper for setting a success message on DRF responses.

The ApiRenderer wraps every response in the standard envelope automatically.
This helper lets views attach a custom `message` that the renderer picks up
and places in the `message` field — useful for toast notifications.

Usage in views:
    from common.response import ApiResponse

    class UserViewSet(viewsets.ModelViewSet):
        def create(self, request, *args, **kwargs):
            user = create_user(request.data)
            serializer = self.get_serializer(user)
            return ApiResponse(
                serializer.data,
                status=status.HTTP_201_CREATED,
                message="User created successfully.",
            )

If you don't need a custom message, use DRF's normal Response — the
renderer wraps it with message=null, which is fine for GET endpoints.
"""

from rest_framework.response import Response


class ApiResponse(Response):
    """
    DRF Response subclass that carries an optional `api_message`.

    The ApiRenderer reads `response.api_message` and places it in the
    envelope's `message` field. Everything else works exactly like
    a standard DRF Response.
    """

    def __init__(
        self,
        data=None,
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=None,
        *,
        message: str | None = None,
    ):
        super().__init__(
            data=data,
            status=status,
            template_name=template_name,
            headers=headers,
            exception=exception,
            content_type=content_type,
        )
        self.api_message = message
