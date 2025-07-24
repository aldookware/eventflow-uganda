from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketTypeViewSet

app_name = 'tickets'

router = DefaultRouter()
router.register('types', TicketTypeViewSet, basename='ticket-types')

urlpatterns = [
    # Event-specific ticket types
    path('event/<uuid:event_id>/', include(router.urls)),
]
