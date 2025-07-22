from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from decimal import Decimal
import uuid
import string
import random

User = get_user_model()


def generate_booking_reference():
    """Generate a unique booking reference"""
    prefix = "EF"
    length = 8
    characters = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(characters, k=length))
    return f"{prefix}{suffix}"


class Booking(models.Model):
    """Main booking model representing a complete ticket purchase"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('processing', 'Processing Payment'),
        ('paid', 'Payment Successful'),
        ('failed', 'Payment Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    BOOKING_CHANNELS = [
        ('web', 'Website'),
        ('mobile_app', 'Mobile App'),
        ('admin', 'Admin Panel'),
        ('api', 'API'),
        ('phone', 'Phone'),
        ('walk_in', 'Walk-in'),
        ('partner', 'Partner'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=20, unique=True, default=generate_booking_reference)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    
    # Contact information (may differ from user)
    customer_email = models.EmailField(validators=[EmailValidator()])
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_first_name = models.CharField(max_length=100)
    customer_last_name = models.CharField(max_length=100)
    
    # Billing information
    billing_address = models.TextField(blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_country = models.CharField(max_length=100, default='Uganda')
    billing_postal_code = models.CharField(max_length=20, blank=True)
    
    # Pricing details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_fee_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    
    # Discount and promotional codes
    discount_code = models.ForeignKey('payments.DiscountCode', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    discount_code_used = models.CharField(max_length=100, blank=True, help_text="Store code even if discount is deleted")
    
    # Status and tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='pending')
    booking_channel = models.CharField(max_length=20, choices=BOOKING_CHANNELS, default='web')
    
    # Timing
    booking_expires_at = models.DateTimeField(null=True, blank=True, help_text="When unpaid booking expires")
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_bookings')
    
    # Special requests and notes
    special_requests = models.TextField(blank=True, help_text="Customer requests (dietary, accessibility, etc.)")
    internal_notes = models.TextField(blank=True, help_text="Internal notes for organizers")
    customer_notes = models.TextField(blank=True, help_text="Additional notes from customer")
    
    # Marketing and analytics
    referral_source = models.CharField(max_length=200, blank=True, help_text="How customer found the event")
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    
    # Delivery preferences
    delivery_method = models.CharField(max_length=50, default='electronic', choices=[
        ('electronic', 'Electronic Tickets'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('mobile_app', 'Mobile App'),
        ('print_at_home', 'Print at Home'),
        ('will_call', 'Will Call'),
        ('postal', 'Postal Mail'),
    ])
    
    # Group booking information
    is_group_booking = models.BooleanField(default=False)
    group_size = models.PositiveIntegerField(default=1)
    group_leader_name = models.CharField(max_length=200, blank=True)
    group_leader_contact = models.CharField(max_length=100, blank=True)
    
    # Session and device tracking
    session_id = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    
    # Fraud prevention
    risk_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(1)])
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_bookings')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['event']),
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.event.title}"

    @property
    def customer_full_name(self):
        """Get full name of customer"""
        return f"{self.customer_first_name} {self.customer_last_name}"

    @property
    def total_tickets(self):
        """Get total number of tickets in booking"""
        return sum(item.quantity for item in self.items.all())

    @property
    def is_expired(self):
        """Check if booking has expired"""
        if self.booking_expires_at:
            return timezone.now() > self.booking_expires_at
        return False

    @property
    def is_refundable(self):
        """Check if booking can be refunded"""
        if self.status not in ['paid', 'confirmed']:
            return False
        
        # Check if event allows refunds
        if not any(ticket.ticket_type.is_refundable for ticket in self.tickets.all()):
            return False
        
        # Check refund deadline
        now = timezone.now()
        for ticket in self.tickets.all():
            if ticket.ticket_type.refund_deadline:
                if now > ticket.ticket_type.refund_deadline:
                    return False
            else:
                # Default: 24 hours before event
                if self.event.start_date - now < timezone.timedelta(hours=24):
                    return False
        
        return True

    @property
    def can_be_transferred(self):
        """Check if tickets in booking can be transferred"""
        return any(ticket.is_transferable for ticket in self.tickets.all())

    @property
    def service_fee_percentage(self):
        """Calculate service fee percentage"""
        if self.subtotal > 0:
            return (self.service_fee_total / self.subtotal) * 100
        return 0

    @property
    def tax_percentage(self):
        """Calculate tax percentage"""
        if self.subtotal > 0:
            return (self.tax_total / self.subtotal) * 100
        return 0

    def calculate_totals(self):
        """Recalculate booking totals based on items"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.service_fee_total = sum(item.service_fee_total for item in self.items.all())
        self.tax_total = sum(item.tax_total for item in self.items.all())
        
        # Apply discount
        subtotal_after_discount = self.subtotal - self.discount_amount
        total_before_fees = max(0, subtotal_after_discount)
        
        self.total_amount = total_before_fees + self.service_fee_total + self.tax_total
        self.save(update_fields=['subtotal', 'service_fee_total', 'tax_total', 'total_amount'])

    def apply_discount_code(self, discount_code):
        """Apply a discount code to the booking"""
        if discount_code and discount_code.is_valid_for_booking(self):
            discount_amount = discount_code.calculate_discount(self.subtotal)
            self.discount_code = discount_code
            self.discount_code_used = discount_code.code
            self.discount_amount = discount_amount
            self.calculate_totals()
            
            # Mark discount code as used
            discount_code.times_used += 1
            discount_code.save(update_fields=['times_used'])
            return True
        return False

    def confirm_booking(self):
        """Confirm the booking"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            self.save(update_fields=['status', 'confirmed_at'])
            return True
        return False

    def cancel_booking(self, reason="", cancelled_by=None):
        """Cancel the booking"""
        if self.status in ['pending', 'confirmed', 'paid']:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.cancellation_reason = reason
            self.cancelled_by = cancelled_by
            
            save_fields = ['status', 'cancelled_at', 'cancellation_reason']
            if cancelled_by:
                save_fields.append('cancelled_by')
            
            self.save(update_fields=save_fields)
            
            # Cancel associated tickets
            self.tickets.update(status='cancelled')
            return True
        return False

    def mark_as_paid(self):
        """Mark booking as paid"""
        if self.payment_status in ['pending', 'processing']:
            self.payment_status = 'paid'
            self.status = 'paid'
            self.save(update_fields=['payment_status', 'status'])
            return True
        return False

    def expire_booking(self):
        """Expire unpaid booking"""
        if self.status == 'pending' and self.payment_status == 'pending':
            self.status = 'expired'
            self.save(update_fields=['status'])
            
            # Release reserved tickets
            for item in self.items.all():
                item.ticket_type.release_reservation(item.quantity)
            return True
        return False

    def generate_booking_summary(self):
        """Generate booking summary for emails/receipts"""
        summary = {
            'booking_reference': self.booking_reference,
            'event': {
                'title': self.event.title,
                'date': self.event.start_date,
                'venue': self.event.venue.name,
            },
            'customer': {
                'name': self.customer_full_name,
                'email': self.customer_email,
                'phone': self.customer_phone,
            },
            'items': [],
            'totals': {
                'subtotal': float(self.subtotal),
                'service_fee': float(self.service_fee_total),
                'tax': float(self.tax_total),
                'discount': float(self.discount_amount),
                'total': float(self.total_amount),
                'currency': self.currency,
            },
            'payment_status': self.get_payment_status_display(),
            'booking_date': self.created_at,
        }
        
        for item in self.items.all():
            summary['items'].append({
                'ticket_type': item.ticket_type.name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total': float(item.total_price),
            })
        
        return summary

    def save(self, *args, **kwargs):
        # Set booking expiration if not set
        if not self.booking_expires_at and self.status == 'pending':
            self.booking_expires_at = timezone.now() + timezone.timedelta(minutes=15)
        
        super().save(*args, **kwargs)


class BookingItem(models.Model):
    """Individual items in a booking (specific ticket types and quantities)"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='items')
    ticket_type = models.ForeignKey('tickets.TicketType', on_delete=models.CASCADE, related_name='booking_items')
    
    # Quantity and pricing
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per ticket at time of booking")
    service_fee_per_ticket = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_per_ticket = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Calculated totals
    total_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total for this item (quantity * unit_price)")
    service_fee_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='UGX')
    
    # Seating preferences
    seating_preference = models.CharField(max_length=200, blank=True, help_text="Customer seating requests")
    assigned_seats = models.JSONField(default=list, blank=True, help_text="List of assigned seat information")
    
    # Special requirements
    special_requirements = models.TextField(blank=True, help_text="Special needs for these tickets")
    
    # Delivery preferences for this item
    delivery_method = models.CharField(max_length=50, blank=True, help_text="Override booking delivery method")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_items'
        ordering = ['created_at']
        unique_together = ['booking', 'ticket_type']

    def __str__(self):
        return f"{self.booking.booking_reference} - {self.ticket_type.name} x{self.quantity}"

    @property
    def grand_total_per_ticket(self):
        """Total cost per ticket including fees and taxes"""
        return self.unit_price + self.service_fee_per_ticket + self.tax_per_ticket

    @property
    def grand_total(self):
        """Grand total for this item including all fees and taxes"""
        return self.total_price + self.service_fee_total + self.tax_total

    def calculate_totals(self):
        """Calculate all totals for this item"""
        self.total_price = self.unit_price * self.quantity
        self.service_fee_total = self.service_fee_per_ticket * self.quantity
        self.tax_total = self.tax_per_ticket * self.quantity
        self.save(update_fields=['total_price', 'service_fee_total', 'tax_total'])

    def reserve_tickets(self):
        """Reserve tickets for this item"""
        return self.ticket_type.reserve_tickets(self.quantity)

    def release_tickets(self):
        """Release reserved tickets"""
        self.ticket_type.release_reservation(self.quantity)

    def create_tickets(self):
        """Create actual ticket instances after payment"""
        from tickets.models import Ticket
        tickets = []
        
        for i in range(self.quantity):
            # Get seat assignment if available
            seat_info = {}
            if self.assigned_seats and i < len(self.assigned_seats):
                seat_data = self.assigned_seats[i]
                seat_info = {
                    'seat_number': seat_data.get('seat_number', ''),
                    'row_number': seat_data.get('row_number', ''),
                    'section': seat_data.get('section', ''),
                }
            
            ticket = Ticket.objects.create(
                ticket_type=self.ticket_type,
                event=self.booking.event,
                original_buyer=self.booking.user,
                current_holder=self.booking.user,
                booking=self.booking,
                purchase_price=self.unit_price,
                service_fee_paid=self.service_fee_per_ticket,
                tax_paid=self.tax_per_ticket,
                total_paid=self.grand_total_per_ticket,
                currency=self.currency,
                holder_name=self.booking.customer_full_name,
                holder_email=self.booking.customer_email,
                holder_phone=self.booking.customer_phone,
                **seat_info
            )
            tickets.append(ticket)
        
        return tickets

    def save(self, *args, **kwargs):
        # Auto-calculate totals if not set
        if not self.total_price:
            self.calculate_totals()
        
        super().save(*args, **kwargs)


class BookingGuest(models.Model):
    """Additional guests associated with a booking (for group bookings)"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='guests')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    age_category = models.CharField(max_length=20, choices=[
        ('adult', 'Adult'),
        ('child', 'Child'),
        ('infant', 'Infant'),
        ('senior', 'Senior'),
    ], default='adult')
    
    # Special requirements
    dietary_requirements = models.TextField(blank=True)
    accessibility_needs = models.TextField(blank=True)
    special_notes = models.TextField(blank=True)
    
    # Ticket assignment
    assigned_ticket = models.OneToOneField('tickets.Ticket', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_guest')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_guests'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.booking.booking_reference}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class BookingNote(models.Model):
    """Internal notes on bookings for customer service and organizers"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_notes')
    note = models.TextField()
    is_internal = models.BooleanField(default=True, help_text="Internal note not visible to customer")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note on {self.booking.booking_reference} by {self.user.email}"


class BookingStatusHistory(models.Model):
    """Track status changes for bookings"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    automated = models.BooleanField(default=False, help_text="Changed by system vs manual")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'booking_status_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking.booking_reference}: {self.previous_status} → {self.new_status}"


class WaitlistEntry(models.Model):
    """Waitlist for sold-out ticket types"""
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='waitlist_entries')
    ticket_type = models.ForeignKey('tickets.TicketType', on_delete=models.CASCADE, related_name='waitlist_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waitlist_entries')
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    quantity_requested = models.PositiveIntegerField(default=1)
    max_price_willing = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum price willing to pay")
    
    # Notification preferences
    notify_by_email = models.BooleanField(default=True)
    notify_by_sms = models.BooleanField(default=False)
    notify_by_push = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(help_text="Position in waitlist")
    notified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When notification expires")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'waitlist_entries'
        ordering = ['position', 'created_at']
        unique_together = ['event', 'ticket_type', 'user']
        indexes = [
            models.Index(fields=['event', 'ticket_type']),
            models.Index(fields=['position']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Waitlist: {self.user.email} for {self.ticket_type.name} (#{self.position})"

    def notify_availability(self):
        """Notify user that tickets are available"""
        if self.is_active and not self.notified_at:
            self.notified_at = timezone.now()
            self.expires_at = timezone.now() + timezone.timedelta(hours=2)  # 2-hour window
            self.save(update_fields=['notified_at', 'expires_at'])
            
            # TODO: Send notifications via email/SMS/push
            return True
        return False

    def deactivate(self):
        """Remove from waitlist"""
        self.is_active = False
        self.save(update_fields=['is_active'])

    @classmethod
    def get_next_in_line(cls, ticket_type, quantity=1):
        """Get next person in waitlist for given quantity"""
        return cls.objects.filter(
            ticket_type=ticket_type,
            is_active=True,
            quantity_requested__lte=quantity,
            notified_at__isnull=True
        ).first()

    @classmethod
    def notify_waitlist(cls, ticket_type, available_quantity):
        """Notify people on waitlist when tickets become available"""
        waitlist_entries = cls.objects.filter(
            ticket_type=ticket_type,
            is_active=True,
            notified_at__isnull=True,
            quantity_requested__lte=available_quantity
        ).order_by('position')[:5]  # Notify up to 5 people
        
        for entry in waitlist_entries:
            entry.notify_availability()