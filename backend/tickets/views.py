from rest_framework import viewsets, permissions
from rest_framework.response import Response
from .models import TicketType
from .serializers import TicketTypeSerializer


class TicketTypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TicketTypeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        return TicketType.objects.filter(
            event_id=event_id,
            is_active=True
        ).order_by('sort_order', 'price')
