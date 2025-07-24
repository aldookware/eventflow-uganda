from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
import logging

from .models import (
    Booking, BookingItem, BookingGuest, BookingNote, 
    BookingStatusHistory, WaitlistEntry
)
from .serializers import (
    BookingListSerializer, BookingDetailSerializer, BookingCreateSerializer,
    BookingUpdateSerializer, WaitlistEntrySerializer, WaitlistCreateSerializer,
    AdminBookingListSerializer, BookingAnalyticsSerializer, BookingNoteSerializer
)
from events.permissions import IsOwnerOrReadOnly, IsEventOwnerOrAdmin
from payments.models import Payment

logger = logging.getLogger(__name__)


class BookingListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'booking_channel', 'event']
    search_fields = ['booking_reference', 'customer_email', 'event__title']
    ordering_fields = ['created_at', 'total_amount', 'confirmed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related('event', 'event__venue')


class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'booking_reference'
    
    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related(
            'event', 'event__venue', 'event__organizer', 'discount_code'
        ).prefetch_related(
            'items__ticket_type', 'guests', 'notes', 'status_history', 'tickets'
        )


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        booking = serializer.save()
        
        # Log booking creation
        logger.info(f"Booking created: {booking.booking_reference} by {self.request.user.email}")
        
        # Create status history entry
        BookingStatusHistory.objects.create(
            booking=booking,
            previous_status='',
            new_status='pending',
            changed_by=self.request.user,
            reason='Booking created',
            automated=False
        )


class BookingUpdateView(generics.UpdateAPIView):
    serializer_class = BookingUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'booking_reference'
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        old_booking = self.get_object()
        booking = serializer.save()
        
        # Log the update
        logger.info(f"Booking updated: {booking.booking_reference} by {self.request.user.email}")


class BookingCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def post(self, request, booking_reference):
        try:
            booking = Booking.objects.get(
                booking_reference=booking_reference,
                user=request.user
            )
            
            reason = request.data.get('reason', 'Cancelled by customer')
            
            if booking.cancel_booking(reason=reason, cancelled_by=request.user):
                # Create status history
                BookingStatusHistory.objects.create(
                    booking=booking,
                    previous_status=booking.status,
                    new_status='cancelled',
                    changed_by=request.user,
                    reason=reason,
                    automated=False
                )
                
                return Response({
                    'message': 'Booking cancelled successfully.',
                    'booking_reference': booking.booking_reference,
                    'status': booking.status
                })
            else:
                return Response(
                    {'error': 'Booking cannot be cancelled in its current state.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


# Waitlist Views
class WaitlistListView(generics.ListAPIView):
    serializer_class = WaitlistEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'ticket_type', 'is_active']
    ordering_fields = ['position', 'created_at']
    ordering = ['position']
    
    def get_queryset(self):
        return WaitlistEntry.objects.filter(user=self.request.user)


class WaitlistCreateView(generics.CreateAPIView):
    serializer_class = WaitlistCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class WaitlistDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return WaitlistEntry.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        instance.deactivate()


# Booking Actions
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_booking(request, booking_reference):
    """Manually confirm a booking (admin or organizer action)"""
    try:
        booking = Booking.objects.get(booking_reference=booking_reference)
        
        # Check permissions
        if not (request.user == booking.user or 
                request.user == booking.event.organizer or 
                request.user.role == 'admin'):
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.confirm_booking():
            BookingStatusHistory.objects.create(
                booking=booking,
                previous_status='pending',
                new_status='confirmed',
                changed_by=request.user,
                reason='Manually confirmed',
                automated=False
            )
            
            return Response({
                'message': 'Booking confirmed successfully.',
                'booking_reference': booking.booking_reference,
                'status': booking.status
            })
        else:
            return Response(
                {'error': 'Booking cannot be confirmed in its current state.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def booking_summary(request, booking_reference):
    """Get booking summary for receipts/confirmations"""
    try:
        booking = Booking.objects.get(
            booking_reference=booking_reference,
            user=request.user
        )
        
        summary = booking.generate_booking_summary()
        return Response(summary)
        
    except Booking.DoesNotExist:
        return Response(
            {'error': 'Booking not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


# Analytics
class BookingAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_bookings = Booking.objects.filter(user=request.user)
        
        # Calculate analytics
        total_bookings = user_bookings.count()
        confirmed_bookings = user_bookings.filter(status__in=['confirmed', 'paid']).count()
        cancelled_bookings = user_bookings.filter(status='cancelled').count()
        
        total_revenue = user_bookings.filter(
            payment_status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        average_booking_value = user_bookings.filter(
            payment_status='paid'
        ).aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        total_tickets_sold = user_bookings.aggregate(
            total=Sum('items__quantity')
        )['total'] or 0
        
        conversion_rate = (confirmed_bookings / total_bookings * 100) if total_bookings > 0 else 0
        refund_rate = (user_bookings.filter(status='refunded').count() / total_bookings * 100) if total_bookings > 0 else 0
        
        analytics_data = {
            'total_bookings': total_bookings,
            'confirmed_bookings': confirmed_bookings,
            'cancelled_bookings': cancelled_bookings,
            'total_revenue': total_revenue,
            'average_booking_value': average_booking_value,
            'total_tickets_sold': total_tickets_sold,
            'conversion_rate': round(conversion_rate, 2),
            'refund_rate': round(refund_rate, 2),
        }
        
        serializer = BookingAnalyticsSerializer(analytics_data)
        return Response(serializer.data)


# Organizer Views (for event organizers to see their event bookings)
class OrganizerBookingListView(generics.ListAPIView):
    serializer_class = BookingListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'booking_channel', 'event']
    search_fields = ['booking_reference', 'customer_email', 'customer_first_name', 'customer_last_name']
    ordering_fields = ['created_at', 'total_amount', 'confirmed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        # Only show bookings for events the user organizes
        return Booking.objects.filter(
            event__organizer=self.request.user
        ).select_related('event', 'event__venue', 'user')


# Admin Views
class AdminBookingListView(generics.ListAPIView):
    queryset = Booking.objects.all().select_related(
        'event', 'event__organizer', 'user'
    ).order_by('-created_at')
    serializer_class = AdminBookingListSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_status', 'booking_channel', 'is_flagged', 'event']
    search_fields = ['booking_reference', 'customer_email', 'event__title', 'user__email']
    ordering_fields = ['created_at', 'total_amount', 'confirmed_at', 'risk_score']


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_booking_availability(request):
    """Check if tickets are still available for booking"""
    event_id = request.data.get('event_id')
    items = request.data.get('items', [])  # [{'ticket_type_id': uuid, 'quantity': int}]
    
    if not event_id or not items:
        return Response(
            {'error': 'event_id and items are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    availability_status = {}
    all_available = True
    
    for item in items:
        ticket_type_id = item.get('ticket_type_id')
        quantity = item.get('quantity', 1)
        
        try:
            from tickets.models import TicketType
            ticket_type = TicketType.objects.get(id=ticket_type_id, event_id=event_id)
            
            is_available = ticket_type.can_purchase(quantity)
            availability_status[str(ticket_type_id)] = {
                'available': is_available,
                'requested_quantity': quantity,
                'available_quantity': ticket_type.available_count,
                'ticket_type_name': ticket_type.name,
                'current_price': float(ticket_type.current_price),
                'message': 'Available' if is_available else f'Only {ticket_type.available_count} tickets available'
            }
            
            if not is_available:
                all_available = False
                
        except TicketType.DoesNotExist:
            availability_status[str(ticket_type_id)] = {
                'available': False,
                'message': 'Ticket type not found'
            }
            all_available = False
    
    return Response({
        'all_available': all_available,
        'availability_status': availability_status,
        'checked_at': timezone.now().isoformat()
    })
