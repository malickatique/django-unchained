"""
Custom DRF renderer that wraps every response in the standard API envelope.

Registered in settings via:
    REST_FRAMEWORK = {
        "DEFAULT_RENDERER_CLASSES": ["common.response.renderers.ApiRenderer"],
    }

This is the "invisible wrapper" approach — view code returns plain
Response(data, status=200) and the renderer adds the envelope automatically.
Views never need to construct {success, message, data, meta, errors} themselves.

The renderer detects:
    - Error responses (already enveloped by exception handler) → pass through
    - Paginated responses (contain "results" + "count" keys) → restructure into meta.pagination
    - Regular responses → wrap in {success: true, data: ...}
    - 204 No Content → empty body, no envelope
"""

from rest_framework.renderers import JSONRenderer


class ApiRenderer(JSONRenderer):
    """
    Wraps all JSON responses in the standard API envelope.

    Success shape:
        {
            "success": true,
            "message": <str or null>,
            "data": <object, list, or null>,
            "meta": {},
            "errors": null
        }

    Paginated success shape:
        {
            "success": true,
            "message": null,
            "data": [...],
            "meta": {
                "pagination": {
                    "page": 1, "page_size": 20, "total_pages": 5,
                    "total_records": 97, "has_next": true, ...
                }
            },
            "errors": null
        }

    Error shape (built by exception handler, passed through here):
        {
            "success": false,
            "message": "...",
            "data": null,
            "meta": {},
            "errors": {"code": "...", "details": [...]}
        }
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (
            renderer_context.get("response") if renderer_context else None
        )

        # 204 No Content — return empty body
        if response and response.status_code == 204:
            return b""

        # Already enveloped by exception handler — pass through
        if (
            isinstance(data, dict)
            and "success" in data
            and "errors" in data
        ):
            return super().render(data, accepted_media_type, renderer_context)

        # Error status but NOT yet enveloped (edge case: DRF internals
        # that somehow bypassed our exception handler)
        if response and response.status_code >= 400:
            envelope = {
                "success": False,
                "message": self._extract_fallback_message(data),
                "data": None,
                "meta": {},
                "errors": {
                    "code": "SYSTEM_ERROR",
                    "details": [],
                },
            }
            return super().render(envelope, accepted_media_type, renderer_context)

        # Paginated response — DRF pagination classes return
        # {"count": N, "next": url, "previous": url, "results": [...]}
        if (
            isinstance(data, dict)
            and "results" in data
            and "count" in data
        ):
            envelope = {
                "success": True,
                "message": None,
                "data": data["results"],
                "meta": {
                    "pagination": {
                        "page": self._extract_page_number(data, renderer_context),
                        "page_size": len(data["results"]),
                        "total_pages": self._calculate_total_pages(data),
                        "total_records": data["count"],
                        "has_next": data.get("next") is not None,
                        "has_previous": data.get("previous") is not None,
                        "next": data.get("next"),
                        "previous": data.get("previous"),
                    },
                },
                "errors": None,
            }
            return super().render(envelope, accepted_media_type, renderer_context)

        # Regular success — single object or non-paginated list
        # Check if view set a custom message via ApiResponse helper
        message = None
        if response and hasattr(response, "api_message"):
            message = response.api_message

        envelope = {
            "success": True,
            "message": message,
            "data": data,
            "meta": {},
            "errors": None,
        }
        return super().render(envelope, accepted_media_type, renderer_context)

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_page_number(data: dict, renderer_context: dict | None) -> int:
        """Derive current page from the request query params."""
        if renderer_context:
            request = renderer_context.get("request")
            if request:
                try:
                    return int(request.query_params.get("page", 1))
                except (ValueError, TypeError):
                    pass
        return 1

    @staticmethod
    def _calculate_total_pages(data: dict) -> int:
        """Calculate total pages from count and results length."""
        count = data.get("count", 0)
        page_size = len(data.get("results", []))
        if page_size == 0:
            return 0
        return (count + page_size - 1) // page_size

    @staticmethod
    def _extract_fallback_message(data) -> str:
        """Best-effort message extraction for un-enveloped error responses."""
        if isinstance(data, dict):
            for key in ("detail", "message", "error"):
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        return str(val[0]) if val else "An error occurred."
                    return str(val)
        if isinstance(data, str):
            return data
        return "An error occurred."
