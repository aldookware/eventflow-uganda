from rest_framework import serializers
from django.utils import timezone
from .models import TicketType, Ticket, TicketTransfer, TicketAddOn, TicketAddonPurchase


class TicketTypeSerializer(serializers.ModelSerializer):
    available_count = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()
    current_price = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    gross_revenue = serializers.ReadOnlyField()
    
    class Meta:
        model = TicketType
        fields = [
            'id', 'name', 'description', 'ticket_type', 'price', 'currency',
            'service_fee', 'tax_percentage', 'quantity', 'sold_count',
            'reserved_count', 'available_count', 'min_purchase', 'max_purchase',
            'sale_starts', 'sale_ends', 'early_bird_until', 'early_bird_price',
            'venue_section', 'includes_drink', 'includes_food', 'includes_parking',
            'includes_merchandise', 'perks_description', 'is_refundable',
            'is_transferable', 'refund_deadline', 'transfer_fee', 'sale_status',
            'is_active', 'is_hidden', 'requires_approval', 'age_restriction',
            'special_requirements', 'sort_order', 'display_color',
            'is_available', 'is_sold_out', 'current_price', 'total_price',
            'gross_revenue', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'sold_count', 'reserved_count', 'available_count', 'sale_status',
            'gross_revenue', 'created_at', 'updated_at'
        ]


class TicketTypeCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = [
            'name', 'description', 'ticket_type', 'price', 'currency',
            'cost_price', 'service_fee', 'tax_percentage', 'quantity',
            'min_purchase', 'max_purchase', 'sale_starts', 'sale_ends',
            'early_bird_until', 'early_bird_price', 'seating_plan',
            'venue_section', 'includes_drink', 'includes_food',
            'includes_parking', 'includes_merchandise', 'perks_description',
            'is_refundable', 'is_transferable', 'refund_deadline',
            'transfer_fee', 'is_active', 'is_hidden', 'requires_approval',
            'age_restriction', 'special_requirements', 'access_code',
            'sort_order', 'display_color'
        ]
    
    def validate(self, attrs):
        if attrs.get('sale_starts') and attrs.get('sale_ends'):
            if attrs['sale_starts'] >= attrs['sale_ends']:
                raise serializers.ValidationError(
                    "Sale end date must be after sale start date."
                )
        
        if attrs.get('early_bird_until') and attrs.get('sale_starts'):
            if attrs['early_bird_until'] <= attrs['sale_starts']:
                raise serializers.ValidationError(
                    "Early bird end date must be after sale start date."
                )
        
        if attrs.get('refund_deadline') and attrs.get('sale_ends'):
            if attrs['refund_deadline'] <= attrs['sale_ends']:
                raise serializers.ValidationError(
                    "Refund deadline should be after sale end date."
                )
        
        return attrs


class TicketAddonPurchaseSerializer(serializers.ModelSerializer):
    addon_name = serializers.CharField(source='addon.name', read_only=True)
    addon_type = serializers.CharField(source='addon.addon_type', read_only=True)
    
    class Meta:
        model = TicketAddonPurchase
        fields = [
            'id', 'addon', 'addon_name', 'addon_type', 'quantity',
            'unit_price', 'total_price', 'currency', 'is_delivered',
            'delivery_notes', 'created_at'
        ]
        read_only_fields = ['total_price', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.start_date', read_only=True)
    venue_name = serializers.CharField(source='event.venue.name', read_only=True)
    organizer_name = serializers.CharField(source='event.organizer.full_name', read_only=True)
    current_holder_name = serializers.CharField(source='current_holder.full_name', read_only=True)
    addon_purchases = TicketAddonPurchaseSerializer(many=True, read_only=True)
    is_valid = serializers.ReadOnlyField()
    is_transferable = serializers.ReadOnlyField()
    is_refundable = serializers.ReadOnlyField()
    seat_info = serializers.ReadOnlyField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_code', 'ticket_type_name', 'event_title',
            'event_date', 'venue_name', 'organizer_name', 'current_holder_name',
            'purchase_price', 'service_fee_paid', 'tax_paid', 'total_paid',
            'currency', 'seat_number', 'row_number', 'section', 'seat_info',
            'entry_method', 'qr_code_data', 'status', 'is_checked_in',
            'check_in_time', 'check_in_location', 'transfer_count',
            'last_transfer_date', 'is_vip', 'is_complimentary',
            'special_notes', 'holder_name', 'holder_email', 'holder_phone',
            'is_valid', 'is_transferable', 'is_refundable', 'addon_purchases',
            'created_at', 'updated_at', 'expires_at'
        ]
        read_only_fields = [
            'ticket_code', 'qr_code_data', 'status', 'is_checked_in',
            'check_in_time', 'check_in_location', 'transfer_count',
            'last_transfer_date', 'created_at', 'updated_at'
        ]


class TicketTransferSerializer(serializers.ModelSerializer):
    from_user_name = serializers.CharField(source='from_user.full_name', read_only=True)
    to_user_name = serializers.CharField(source='to_user.full_name', read_only=True)
    ticket_code = serializers.CharField(source='ticket.ticket_code', read_only=True)
    
    class Meta:
        model = TicketTransfer
        fields = [
            'id', 'ticket_code', 'from_user_name', 'to_user_name',
            'transfer_fee', 'reason', 'is_approved', 'created_at'
        ]
        read_only_fields = ['from_user_name', 'to_user_name', 'ticket_code', 'created_at']


class TicketTransferCreateSerializer(serializers.Serializer):
    to_user_email = serializers.EmailField()
    reason = serializers.CharField(max_length=200, required=False, allow_blank=True)
    
    def validate_to_user_email(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No user found with this email address."
            )
        return value
    
    def validate(self, attrs):
        ticket = self.context['ticket']
        request_user = self.context['request'].user
        
        if ticket.current_holder != request_user:
            raise serializers.ValidationError(
                "You can only transfer tickets you currently hold."
            )
        
        if not ticket.is_transferable:
            raise serializers.ValidationError(
                "This ticket cannot be transferred."
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        to_user = User.objects.get(email=attrs['to_user_email'])
        
        if to_user == request_user:
            raise serializers.ValidationError(
                "You cannot transfer a ticket to yourself."
            )
        
        return attrs


class TicketCheckInSerializer(serializers.Serializer):
    ticket_code = serializers.CharField()
    location = serializers.CharField(required=False, allow_blank=True)
    
    def validate_ticket_code(self, value):
        if not Ticket.objects.filter(ticket_code=value).exists():
            raise serializers.ValidationError("Invalid ticket code.")
        return value
    
    def validate(self, attrs):
        ticket = Ticket.objects.get(ticket_code=attrs['ticket_code'])
        
        if not ticket.is_valid:
            raise serializers.ValidationError(
                f"Ticket is not valid for check-in. Status: {ticket.get_status_display()}"
            )
        
        if ticket.is_checked_in:
            raise serializers.ValidationError("Ticket has already been checked in.")
        
        # Verify event is today or ongoing
        now = timezone.now()
        event = ticket.event
        
        if event.end_date < now:
            raise serializers.ValidationError("Event has already ended.")
        
        # Allow check-in from 2 hours before event starts
        check_in_allowed_from = event.start_date - timezone.timedelta(hours=2)
        if now < check_in_allowed_from:
            raise serializers.ValidationError(
                f"Check-in not yet available. Check-in opens at {check_in_allowed_from.strftime('%Y-%m-%d %H:%M')}."
            )
        
        attrs['ticket'] = ticket
        return attrs


class TicketAddOnSerializer(serializers.ModelSerializer):
    remaining_quantity = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = TicketAddOn
        fields = [
            'id', 'name', 'addon_type', 'description', 'price', 'currency',
            'quantity_available', 'quantity_sold', 'remaining_quantity',
            'max_per_ticket', 'is_mandatory', 'image', 'is_active',
            'is_available', 'sort_order', 'created_at'
        ]
        read_only_fields = ['quantity_sold', 'remaining_quantity', 'created_at']


# Admin serializers
class AdminTicketListSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    organizer_email = serializers.CharField(source='event.organizer.email', read_only=True)
    current_holder_email = serializers.CharField(source='current_holder.email', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_code', 'ticket_type_name', 'event_title',
            'organizer_email', 'current_holder_email', 'status',
            'is_checked_in', 'check_in_time', 'total_paid', 'currency',
            'is_vip', 'is_complimentary', 'created_at'
        ]


class TicketAnalyticsSerializer(serializers.Serializer):
    """Serializer for ticket analytics data"""
    total_tickets_created = serializers.IntegerField()
    tickets_sold = serializers.IntegerField()  
    tickets_checked_in = serializers.IntegerField()
    tickets_transferred = serializers.IntegerField()
    tickets_refunded = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_ticket_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    check_in_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    transfer_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    refund_rate = serializers.DecimalField(max_digits=5, decimal_places=2)