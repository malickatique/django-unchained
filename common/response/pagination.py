"""
Custom pagination classes for the API.

Page-number pagination is the default for all list endpoints.
Cursor pagination can be added later for high-volume feeds that need
stable ordering under concurrent writes.

The pagination class returns DRF's standard paginated dict:
    {"count": N, "next": url, "previous": url, "results": [...]}

The ApiRenderer then restructures this into the envelope's meta.pagination
block. This separation keeps pagination logic clean and testable.
"""

from rest_framework.pagination import PageNumberPagination


class ApiPageNumberPagination(PageNumberPagination):
    """
    Default page-number pagination for all list endpoints.

    Query params:
        ?page=1          (1-based, default 1)
        ?page_size=20    (client can override, capped at max_page_size)
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"
