import threading

from common.logging.context import RequestContext

_thread_local = threading.local()


def get_current_user_id():
    """
    Retrieve the current authenticated user's UUID from thread-local storage.
    Returns None if no user is set (anonymous requests, Celery tasks, commands).

    This is the same pattern as Spring's SecurityContextHolder.getContext()
    or Laravel's Auth::id() — but explicit via thread-local since Django
    models don't have access to the HTTP request.
    """
    return getattr(_thread_local, "current_user_id", None)


def set_current_user_id(user_id):
    """Manually set user ID — useful in Celery tasks or management commands."""
    _thread_local.current_user_id = user_id


class AuditMiddleware:
    """
    Injects the authenticated user's UUID into thread-local storage so that
    AuditModel.save() can auto-populate created_by / updated_by.

    Also enriches the logging RequestContext with auth fields. This is
    belt-and-suspenders with RequestLoggingMiddleware's own auth enrichment —
    handles edge cases where DRF token/JWT authentication is resolved in the
    view layer (after Django's AuthenticationMiddleware has already run).

    Add to MIDDLEWARE in settings:
        'common.middleware.AuditMiddleware',

    Must come AFTER AuthenticationMiddleware and RequestLoggingMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set user ID if authenticated
        if hasattr(request, "user") and request.user.is_authenticated:
            user = request.user
            _thread_local.current_user_id = user.id

            # Enrich logging context with auth details
            RequestContext.update(
                auth_user_id=str(user.id),
                auth_user_type=getattr(user, "user_type", None),
                organisation_id=str(user.organisation_id)
                if getattr(user, "organisation_id", None)
                else None,
            )
        else:
            _thread_local.current_user_id = None

        response = self.get_response(request)

        # Clean up after request to prevent leakage across requests
        # in the same thread (important for WSGI servers like Gunicorn)
        _thread_local.current_user_id = None

        return response
