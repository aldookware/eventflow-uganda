from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from .models import (
    Booking, BookingItem, BookingGuest, BookingNote, 
    BookingStatusHistory, WaitlistEntry
)
from tickets.models import TicketType, Ticket
from events.models import Event
from users.serializers import UserProfileSerializer


class BookingItemSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    grand_total = serializers.ReadOnlyField()
    
    class Meta:
        model = BookingItem
        fields = [
            'id', 'ticket_type', 'ticket_type_name', 'quantity', 'unit_price',
            'service_fee_per_ticket', 'tax_per_ticket', 'total_price',
            'service_fee_total', 'tax_total', 'grand_total', 'currency',
            'seating_preference', 'assigned_seats', 'special_requirements'
        ]
        read_only_fields = ['total_price', 'service_fee_total', 'tax_total']


class BookingGuestSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = BookingGuest
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'age_category', 'dietary_requirements', 'accessibility_needs',
            'special_notes'
        ]


class BookingNoteSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = BookingNote
        fields = ['id', 'user_name', 'note', 'is_internal', 'created_at']
        read_only_fields = ['user_name', 'created_at']


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)
    
    class Meta:
        model = BookingStatusHistory
        fields = [
            'id', 'previous_status', 'new_status', 'changed_by_name',
            'reason', 'automated', 'created_at'
        ]


class BookingListSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.start_date', read_only=True)
    venue_name = serializers.CharField(source='event.venue.name', read_only=True)
    customer_full_name = serializers.ReadOnlyField()
    total_tickets = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    is_refundable = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'event_title', 'event_date', 'venue_name',
            'customer_full_name', 'customer_email', 'total_tickets', 'total_amount',
            'currency', 'status', 'payment_status', 'booking_channel',
            'is_expired', 'is_refundable', 'created_at', 'confirmed_at'
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    event = serializers.SerializerMethodField()
    items = BookingItemSerializer(many=True, read_only=True)
    guests = BookingGuestSerializer(many=True, read_only=True)
    notes = BookingNoteSerializer(many=True, read_only=True)
    status_history = BookingStatusHistorySerializer(many=True, read_only=True)
    tickets = serializers.SerializerMethodField()
    customer_full_name = serializers.ReadOnlyField()
    total_tickets = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    is_refundable = serializers.ReadOnlyField()
    can_be_transferred = serializers.ReadOnlyField()
    service_fee_percentage = serializers.ReadOnlyField()
    tax_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'event', 'customer_email', 'customer_phone',
            'customer_first_name', 'customer_last_name', 'customer_full_name',
            'billing_address', 'billing_city', 'billing_country', 'billing_postal_code',
            'subtotal', 'service_fee_total', 'tax_total', 'discount_amount',
            'total_amount', 'currency', 'discount_code_used', 'status', 'payment_status',
            'booking_channel', 'booking_expires_at', 'confirmed_at', 'cancelled_at',
            'cancellation_reason', 'special_requests', 'customer_notes',
            'delivery_method', 'is_group_booking', 'group_size',
            'total_tickets', 'is_expired', 'is_refundable', 'can_be_transferred',
            'service_fee_percentage', 'tax_percentage', 'items', 'guests', 'notes',
            'status_history', 'tickets', 'created_at', 'updated_at'
        ]
    
    def get_event(self, obj):
        from events.serializers import EventListSerializer
        return EventListSerializer(obj.event).data
    
    def get_tickets(self, obj):
        from tickets.serializers import TicketSerializer
        return TicketSerializer(obj.tickets.all(), many=True).data


class BookingCreateSerializer(serializers.ModelSerializer):
    items = BookingItemSerializer(many=True)
    guests = BookingGuestSerializer(many=True, required=False)
    
    class Meta:
        model = Booking
        fields = [
            'event', 'customer_email', 'customer_phone', 'customer_first_name',
            'customer_last_name', 'billing_address', 'billing_city',
            'billing_country', 'billing_postal_code', 'special_requests',
            'customer_notes', 'delivery_method', 'is_group_booking',
            'group_size', 'group_leader_name', 'group_leader_contact',
            'referral_source', 'utm_source', 'utm_medium', 'utm_campaign',
            'items', 'guests'
        ]
    
    def validate(self, attrs):
        event = attrs.get('event')
        items = attrs.get('items', [])
        
        if not items:
            raise serializers.ValidationError("At least one ticket item is required.")
        
        # Validate ticket availability
        for item_data in items:
            ticket_type = item_data['ticket_type']
            quantity = item_data['quantity']
            
            if ticket_type.event != event:
                raise serializers.ValidationError(
                    f"Ticket type {ticket_type.name} does not belong to the selected event."
                )
            
            if not ticket_type.can_purchase(quantity):
                raise serializers.ValidationError(
                    f"Cannot purchase {quantity} tickets of type {ticket_type.name}. "
                    f"Available: {ticket_type.available_count}"
                )
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        guests_data = validated_data.pop('guests', [])
        
        # Create booking
        booking = Booking.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        
        # Create booking items and reserve tickets
        total_service_fee = Decimal('0.00')
        total_tax = Decimal('0.00')
        subtotal = Decimal('0.00')
        
        for item_data in items_data:
            ticket_type = item_data['ticket_type']
            quantity = item_data['quantity']
            
            # Reserve tickets
            if not ticket_type.reserve_tickets(quantity):
                raise serializers.ValidationError(
                    f"Could not reserve {quantity} tickets for {ticket_type.name}"
                )
            
            # Calculate pricing
            unit_price = ticket_type.current_price
            service_fee_per_ticket = ticket_type.service_fee
            tax_per_ticket = unit_price * (ticket_type.tax_percentage / 100)
            
            item = BookingItem.objects.create(
                booking=booking,
                ticket_type=ticket_type,
                quantity=quantity,
                unit_price=unit_price,
                service_fee_per_ticket=service_fee_per_ticket,
                tax_per_ticket=tax_per_ticket,
                seating_preference=item_data.get('seating_preference', ''),
                special_requirements=item_data.get('special_requirements', ''),
            )
            
            subtotal += item.total_price
            total_service_fee += item.service_fee_total
            total_tax += item.tax_total
        
        # Update booking totals
        booking.subtotal = subtotal
        booking.service_fee_total = total_service_fee
        booking.tax_total = total_tax
        booking.total_amount = subtotal + total_service_fee + total_tax
        booking.save()
        
        # Create guests
        for guest_data in guests_data:
            BookingGuest.objects.create(booking=booking, **guest_data)
        
        return booking


class BookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'customer_email', 'customer_phone', 'customer_first_name',
            'customer_last_name', 'billing_address', 'billing_city',
            'billing_country', 'billing_postal_code', 'special_requests',
            'customer_notes', 'delivery_method'
        ]
    
    def validate(self, attrs):
        booking = self.instance
        if booking.status not in ['pending', 'confirmed']:
            raise serializers.ValidationError(
                "Cannot update booking that is paid, cancelled, or expired."
            )
        return attrs


class WaitlistEntrySerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = WaitlistEntry
        fields = [
            'id', 'event', 'event_title', 'ticket_type', 'ticket_type_name',
            'user_name', 'email', 'phone', 'quantity_requested',
            'max_price_willing', 'notify_by_email', 'notify_by_sms',
            'notify_by_push', 'is_active', 'position', 'created_at'
        ]
        read_only_fields = ['user_name', 'position', 'created_at']


class WaitlistCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitlistEntry
        fields = [
            'event', 'ticket_type', 'email', 'phone', 'quantity_requested',
            'max_price_willing', 'notify_by_email', 'notify_by_sms', 'notify_by_push'
        ]
    
    def validate(self, attrs):
        event = attrs.get('event')
        ticket_type = attrs.get('ticket_type')
        user = self.context['request'].user
        
        if ticket_type.event != event:
            raise serializers.ValidationError(
                "Ticket type does not belong to the selected event."
            )
        
        # Check if user is already on waitlist
        if WaitlistEntry.objects.filter(
            event=event,
            ticket_type=ticket_type,
            user=user,
            is_active=True
        ).exists():
            raise serializers.ValidationError(
                "You are already on the waitlist for this ticket type."
            )
        
        # Check if tickets are actually sold out
        if ticket_type.available_count > 0:
            raise serializers.ValidationError(
                "Tickets are still available for purchase."
            )
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        ticket_type = validated_data['ticket_type']
        
        # Calculate position in waitlist
        last_position = WaitlistEntry.objects.filter(
            ticket_type=ticket_type,
            is_active=True
        ).aggregate(max_position=models.Max('position'))['max_position'] or 0
        
        return WaitlistEntry.objects.create(
            user=user,
            position=last_position + 1,
            **validated_data
        )


# Admin serializers
class AdminBookingListSerializer(serializers.ModelSerializer):
    customer_full_name = serializers.ReadOnlyField()
    event_title = serializers.CharField(source='event.title', read_only=True)
    organizer_name = serializers.CharField(source='event.organizer.full_name', read_only=True)
    total_tickets = serializers.ReadOnlyField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'event_title', 'organizer_name',
            'user_email', 'customer_full_name', 'customer_email',
            'total_tickets', 'total_amount', 'currency', 'status',
            'payment_status', 'booking_channel', 'is_flagged',
            'risk_score', 'created_at', 'confirmed_at'
        ]


class BookingAnalyticsSerializer(serializers.Serializer):
    """Serializer for booking analytics data"""
    total_bookings = serializers.IntegerField()
    confirmed_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_booking_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_tickets_sold = serializers.IntegerField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    refund_rate = serializers.DecimalField(max_digits=5, decimal_places=2)