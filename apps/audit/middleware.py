"""
Audit middleware - logs API requests.
"""


class AuditMiddleware:
    """Log significant API actions."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only log mutating API calls
        if (
            request.path.startswith('/api/') and
            request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and
            hasattr(request, 'user') and
            request.user.is_authenticated
        ):
            try:
                from .models import AuditEvent
                AuditEvent.objects.create(
                    actor=request.user,
                    action=f"api_{request.method.lower()}",
                    entity=request.path,
                    entity_id='',
                    metadata={
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code,
                    },
                    ip_address=self._get_ip(request),
                )
            except Exception:
                pass

        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
