from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import string
import random
from decimal import Decimal

User = get_user_model()


def generate_ticket_code():
    """Generate a unique ticket code"""
    length = 10
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


class TicketType(models.Model):
    """Different types/categories of tickets for events"""
    TICKET_TYPE_CHOICES = [
        ('general', 'General Admission'),
        ('vip', 'VIP'),
        ('premium', 'Premium'),
        ('early_bird', 'Early Bird'),
        ('student', 'Student'),
        ('group', 'Group'),
        ('season', 'Season Pass'),
        ('day_pass', 'Day Pass'),
        ('backstage', 'Backstage Pass'),
        ('meet_greet', 'Meet & Greet'),
        ('table', 'Table Booking'),
        ('standing', 'Standing Room'),
        ('balcony', 'Balcony'),
        ('floor', 'Floor'),
        ('box', 'Box Seats'),
    ]
    
    SALE_STATUS_CHOICES = [
        ('not_started', 'Sale Not Started'),
        ('on_sale', 'On Sale'),
        ('paused', 'Sale Paused'),
        ('sold_out', 'Sold Out'),
        ('ended', 'Sale Ended'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ticket_type = models.CharField(max_length=50, choices=TICKET_TYPE_CHOICES, default='general')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Cost for organizer")
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Quantity and sales
    quantity = models.PositiveIntegerField(help_text="Total tickets available")
    sold_count = models.PositiveIntegerField(default=0)
    reserved_count = models.PositiveIntegerField(default=0, help_text="Tickets temporarily held")
    min_purchase = models.PositiveIntegerField(default=1, help_text="Minimum tickets per order")
    max_purchase = models.PositiveIntegerField(default=10, help_text="Maximum tickets per order")
    
    # Sales period
    sale_starts = models.DateTimeField()
    sale_ends = models.DateTimeField()
    early_bird_until = models.DateTimeField(null=True, blank=True)
    early_bird_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Seating and venue
    seating_plan = models.ForeignKey('events.SeatingPlan', on_delete=models.SET_NULL, null=True, blank=True, related_name='ticket_types')
    venue_section = models.CharField(max_length=100, blank=True, help_text="Specific section in venue")
    
    # Features and perks
    includes_drink = models.BooleanField(default=False)
    includes_food = models.BooleanField(default=False)
    includes_parking = models.BooleanField(default=False)
    includes_merchandise = models.BooleanField(default=False)
    perks_description = models.TextField(blank=True, help_text="What's included with this ticket")
    
    # Policies
    is_refundable = models.BooleanField(default=True)
    is_transferable = models.BooleanField(default=True)
    refund_deadline = models.DateTimeField(null=True, blank=True)
    transfer_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status and visibility
    sale_status = models.CharField(max_length=20, choices=SALE_STATUS_CHOICES, default='not_started')
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False, help_text="Hide from public but allow direct links")
    requires_approval = models.BooleanField(default=False, help_text="Requires organizer approval")
    
    # Special requirements
    age_restriction = models.CharField(max_length=20, blank=True)
    special_requirements = models.TextField(blank=True, help_text="ID requirements, dress code, etc.")
    access_code = models.CharField(max_length=50, blank=True, help_text="Code required to purchase")
    
    # Sorting and display
    sort_order = models.PositiveIntegerField(default=0)
    display_color = models.CharField(max_length=7, default="#007bff", help_text="Hex color for UI display")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ticket_types'
        ordering = ['sort_order', 'price']
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['sale_status']),
            models.Index(fields=['sale_starts', 'sale_ends']),
        ]

    def __str__(self):
        return f"{self.event.title} - {self.name}"

    @property
    def is_available(self):
        """Check if tickets are currently available for purchase"""
        now = timezone.now()
        return (
            self.is_active and 
            self.sale_status == 'on_sale' and
            self.sale_starts <= now <= self.sale_ends and
            self.available_count > 0
        )

    @property
    def available_count(self):
        """Number of tickets available for purchase"""
        return max(0, self.quantity - self.sold_count - self.reserved_count)

    @property
    def is_sold_out(self):
        """Check if ticket type is sold out"""
        return self.available_count == 0

    @property
    def current_price(self):
        """Get current price (early bird or regular)"""
        if (self.early_bird_until and self.early_bird_price and 
            timezone.now() <= self.early_bird_until):
            return self.early_bird_price
        return self.price

    @property
    def total_price(self):
        """Total price including service fee and tax"""
        base_price = self.current_price
        price_with_fee = base_price + self.service_fee
        tax_amount = price_with_fee * (self.tax_percentage / 100)
        return price_with_fee + tax_amount

    @property
    def gross_revenue(self):
        """Total revenue from this ticket type"""
        return Decimal(str(self.sold_count)) * self.current_price

    def can_purchase(self, quantity):
        """Check if given quantity can be purchased"""
        return (
            self.is_available and
            self.min_purchase <= quantity <= self.max_purchase and
            quantity <= self.available_count
        )

    def reserve_tickets(self, quantity):
        """Reserve tickets temporarily"""
        if quantity <= self.available_count:
            self.reserved_count += quantity
            self.save(update_fields=['reserved_count'])
            return True
        return False

    def release_reservation(self, quantity):
        """Release reserved tickets"""
        self.reserved_count = max(0, self.reserved_count - quantity)
        self.save(update_fields=['reserved_count'])

    def sell_tickets(self, quantity):
        """Mark tickets as sold"""
        if quantity <= self.available_count + self.reserved_count:
            if quantity <= self.reserved_count:
                self.reserved_count -= quantity
            else:
                remaining = quantity - self.reserved_count
                self.reserved_count = 0
            self.sold_count += quantity
            
            # Update sale status if sold out
            if self.available_count == 0:
                self.sale_status = 'sold_out'
            
            self.save(update_fields=['sold_count', 'reserved_count', 'sale_status'])
            return True
        return False

    def update_sale_status(self):
        """Update sale status based on current conditions"""
        now = timezone.now()
        
        if not self.is_active:
            self.sale_status = 'ended'
        elif self.available_count == 0:
            self.sale_status = 'sold_out'
        elif now < self.sale_starts:
            self.sale_status = 'not_started'
        elif now > self.sale_ends:
            self.sale_status = 'ended'
        else:
            self.sale_status = 'on_sale'
        
        self.save(update_fields=['sale_status'])


class Ticket(models.Model):
    """Individual ticket instances"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('refunded', 'Refunded'),
        ('transferred', 'Transferred'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    ENTRY_METHODS = [
        ('qr_code', 'QR Code'),
        ('barcode', 'Barcode'),
        ('nfc', 'NFC'),
        ('manual', 'Manual Check'),
        ('mobile', 'Mobile App'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_code = models.CharField(max_length=20, unique=True, default=generate_ticket_code)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='tickets')
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='tickets')
    
    # Ownership
    original_buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='original_tickets')
    current_holder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='held_tickets')
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='tickets')
    
    # Pricing (at time of purchase)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    
    # Seating assignment
    seat_number = models.CharField(max_length=50, blank=True)
    row_number = models.CharField(max_length=20, blank=True)
    section = models.CharField(max_length=100, blank=True)
    
    # Entry and validation
    entry_method = models.CharField(max_length=20, choices=ENTRY_METHODS, default='qr_code')
    qr_code_data = models.TextField(blank=True)
    barcode_data = models.CharField(max_length=200, blank=True)
    nfc_data = models.CharField(max_length=200, blank=True)
    
    # Usage tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_checked_in = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_in_location = models.CharField(max_length=200, blank=True)
    checked_in_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checked_in_tickets')
    
    # Transfer tracking
    transfer_count = models.PositiveIntegerField(default=0)
    last_transfer_date = models.DateTimeField(null=True, blank=True)
    transfer_fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Validation and security
    validation_code = models.CharField(max_length=100, blank=True, help_text="Additional security code")
    is_duplicate_protection = models.BooleanField(default=True)
    anti_fraud_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # Special attributes
    is_vip = models.BooleanField(default=False)
    is_complimentary = models.BooleanField(default=False)
    special_notes = models.TextField(blank=True)
    holder_name = models.CharField(max_length=200, blank=True, help_text="Name on ticket if different from holder")
    holder_email = models.EmailField(blank=True)
    holder_phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_code']),
            models.Index(fields=['event']),
            models.Index(fields=['status']),
            models.Index(fields=['current_holder']),
            models.Index(fields=['is_checked_in']),
        ]
        unique_together = [
            ['event', 'seat_number', 'row_number', 'section'],
        ]

    def __str__(self):
        return f"Ticket {self.ticket_code} - {self.event.title}"

    @property
    def is_valid(self):
        """Check if ticket is valid for use"""
        return (
            self.status == 'active' and
            not self.is_checked_in and
            (not self.expires_at or timezone.now() <= self.expires_at)
        )

    @property
    def is_transferable(self):
        """Check if ticket can be transferred"""
        return (
            self.status == 'active' and
            self.ticket_type.is_transferable and
            not self.is_checked_in and
            self.event.start_date > timezone.now()
        )

    @property
    def is_refundable(self):
        """Check if ticket can be refunded"""
        if not self.ticket_type.is_refundable or self.is_checked_in:
            return False
        
        if self.ticket_type.refund_deadline:
            return timezone.now() <= self.ticket_type.refund_deadline
        
        # Default: allow refund until 24 hours before event
        return self.event.start_date - timezone.now() > timezone.timedelta(hours=24)

    @property
    def seat_info(self):
        """Get formatted seat information"""
        parts = []
        if self.section:
            parts.append(f"Section {self.section}")
        if self.row_number:
            parts.append(f"Row {self.row_number}")
        if self.seat_number:
            parts.append(f"Seat {self.seat_number}")
        return ", ".join(parts) if parts else "General Admission"

    def generate_qr_data(self):
        """Generate QR code data for ticket"""
        data = {
            'ticket_id': str(self.id),
            'ticket_code': self.ticket_code,
            'event_id': str(self.event.id),
            'holder_id': str(self.current_holder.id),
            'validation_code': self.validation_code,
            'issued_at': self.created_at.isoformat(),
        }
        return f"EVENTFLOW:{';'.join([f'{k}={v}' for k, v in data.items()])}"

    def check_in(self, location="", checked_in_by=None):
        """Check in the ticket"""
        if self.is_valid and not self.is_checked_in:
            self.is_checked_in = True
            self.check_in_time = timezone.now()
            self.check_in_location = location
            self.checked_in_by = checked_in_by
            self.status = 'used'
            self.save(update_fields=['is_checked_in', 'check_in_time', 'check_in_location', 'checked_in_by', 'status'])
            return True
        return False

    def transfer_to(self, new_holder, transfer_fee=0):
        """Transfer ticket to new holder"""
        if self.is_transferable:
            old_holder = self.current_holder
            self.current_holder = new_holder
            self.transfer_count += 1
            self.last_transfer_date = timezone.now()
            self.transfer_fee_paid += transfer_fee
            
            save_fields = ['current_holder', 'transfer_count', 'last_transfer_date', 'transfer_fee_paid']
            self.save(update_fields=save_fields)
            
            # Create transfer record
            TicketTransfer.objects.create(
                ticket=self,
                from_user=old_holder,
                to_user=new_holder,
                transfer_fee=transfer_fee
            )
            return True
        return False

    def refund(self, refund_amount=None, reason=""):
        """Process ticket refund"""
        if self.is_refundable:
            self.status = 'refunded'
            self.save(update_fields=['status'])
            
            # Create refund record
            from payments.models import Refund
            refund_amount = refund_amount or self.total_paid
            Refund.objects.create(
                ticket=self,
                original_payment=self.booking.payment,
                refund_amount=refund_amount,
                reason=reason,
                status='pending'
            )
            return True
        return False

    def save(self, *args, **kwargs):
        if not self.qr_code_data:
            self.qr_code_data = self.generate_qr_data()
        
        if not self.validation_code:
            self.validation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        super().save(*args, **kwargs)


class TicketTransfer(models.Model):
    """Track ticket transfers between users"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='transfers')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferred_tickets')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_tickets')
    transfer_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reason = models.CharField(max_length=200, blank=True)
    is_approved = models.BooleanField(default=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transfers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket_transfers'
        ordering = ['-created_at']

    def __str__(self):
        return f"Transfer {self.ticket.ticket_code} from {self.from_user.email} to {self.to_user.email}"


class TicketAddOn(models.Model):
    """Additional items/services that can be purchased with tickets"""
    ADDON_TYPES = [
        ('parking', 'Parking'),
        ('merchandise', 'Merchandise'),
        ('food', 'Food & Beverage'),
        ('vip_package', 'VIP Package'),
        ('meet_greet', 'Meet & Greet'),
        ('photo_package', 'Photo Package'),
        ('premium_seating', 'Premium Seating Upgrade'),
        ('early_entry', 'Early Entry'),
        ('backstage_tour', 'Backstage Tour'),
        ('gift_bag', 'Gift Bag'),
        ('lounge_access', 'Lounge Access'),
        ('fast_track', 'Fast Track Entry'),
    ]
    
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='ticket_addons')
    name = models.CharField(max_length=200)
    addon_type = models.CharField(max_length=50, choices=ADDON_TYPES)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    quantity_available = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    quantity_sold = models.PositiveIntegerField(default=0)
    max_per_ticket = models.PositiveIntegerField(default=1, help_text="Maximum quantity per ticket")
    is_mandatory = models.BooleanField(default=False, help_text="Required for certain ticket types")
    applicable_ticket_types = models.ManyToManyField(TicketType, blank=True, related_name='addons')
    image = models.ImageField(upload_to='ticket_addons/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ticket_addons'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f"{self.event.title} - {self.name}"

    @property
    def is_available(self):
        """Check if addon is available for purchase"""
        if not self.is_active:
            return False
        if self.quantity_available is None:
            return True
        return self.quantity_sold < self.quantity_available

    @property
    def remaining_quantity(self):
        """Get remaining quantity available"""
        if self.quantity_available is None:
            return None
        return max(0, self.quantity_available - self.quantity_sold)


class TicketAddonPurchase(models.Model):
    """Track addon purchases with tickets"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='addon_purchases')
    addon = models.ForeignKey(TicketAddOn, on_delete=models.CASCADE, related_name='purchases')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    is_delivered = models.BooleanField(default=False)
    delivery_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket_addon_purchases'
        unique_together = ['ticket', 'addon']

    def __str__(self):
        return f"{self.ticket.ticket_code} - {self.addon.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)