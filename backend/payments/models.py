from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
import string
import random

User = get_user_model()


def generate_transaction_reference():
    """Generate a unique transaction reference"""
    prefix = "TXN"
    length = 10
    characters = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(characters, k=length))
    return f"{prefix}{suffix}"


class Payment(models.Model):
    """Payment transactions for bookings"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
        ('disputed', 'Disputed'),
        ('expired', 'Expired'),
    ]
    
    PAYMENT_METHODS = [
        ('mobile_money', 'Mobile Money'),
        ('bank_card', 'Bank Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('flutterwave', 'Flutterwave'),
        ('pesapal', 'PesaPal'),
        ('airtel_money', 'Airtel Money'),
        ('mtn_momo', 'MTN Mobile Money'),
        ('agent_banking', 'Agent Banking'),
    ]
    
    MOBILE_MONEY_PROVIDERS = [
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
        ('ugatel', 'UTL Money'),
        ('africell', 'Africell Money'),
    ]
    
    GATEWAY_CHOICES = [
        ('flutterwave', 'Flutterwave'),
        ('pesapal', 'PesaPal'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('direct', 'Direct Payment'),
        ('manual', 'Manual Payment'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_reference = models.CharField(max_length=20, unique=True, default=generate_transaction_reference)
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    mobile_money_provider = models.CharField(max_length=20, choices=MOBILE_MONEY_PROVIDERS, blank=True)
    payment_gateway = models.CharField(max_length=50, choices=GATEWAY_CHOICES, default='flutterwave')
    
    # Gateway transaction details
    gateway_transaction_id = models.CharField(max_length=200, blank=True, help_text="Transaction ID from payment gateway")
    gateway_reference = models.CharField(max_length=200, blank=True, help_text="Gateway's reference number")
    gateway_response = models.JSONField(default=dict, blank=True, help_text="Raw gateway response")
    
    # Customer payment details
    customer_phone = models.CharField(max_length=20, blank=True, help_text="Phone number used for payment")
    customer_email = models.EmailField(blank=True)
    card_last_four = models.CharField(max_length=4, blank=True, help_text="Last 4 digits of card")
    card_type = models.CharField(max_length=20, blank=True, help_text="Visa, MasterCard, etc.")
    
    # Status and tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)
    gateway_callback_received = models.BooleanField(default=False)
    callback_data = models.JSONField(default=dict, blank=True)
    
    # Fees and charges
    gateway_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Fee charged by gateway")
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Our platform fee")
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount after deducting fees")
    
    # Retry and failure handling
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    failure_code = models.CharField(max_length=50, blank=True)
    
    # Settlement information
    is_settled = models.BooleanField(default=False, help_text="Whether payment has been settled to organizer")
    settled_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    settlement_date = models.DateTimeField(null=True, blank=True)
    settlement_reference = models.CharField(max_length=200, blank=True)
    
    # Verification and security
    requires_verification = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('manual_review', 'Manual Review Required'),
    ], default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Fraud detection
    risk_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(1)])
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.TextField(blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=200, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Webhooks and notifications
    webhook_sent = models.BooleanField(default=False)
    webhook_response = models.JSONField(default=dict, blank=True)
    customer_notified = models.BooleanField(default=False)
    organizer_notified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When payment request expires")

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_reference']),
            models.Index(fields=['booking']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_gateway']),
            models.Index(fields=['gateway_transaction_id']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['is_settled']),
        ]

    def __str__(self):
        return f"Payment {self.transaction_reference} - {self.amount} {self.currency}"

    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'completed'

    @property
    def is_pending(self):
        """Check if payment is still pending"""
        return self.status in ['pending', 'processing']

    @property
    def is_failed(self):
        """Check if payment failed"""
        return self.status in ['failed', 'cancelled', 'expired']

    @property
    def can_retry(self):
        """Check if payment can be retried"""
        return (
            self.is_failed and 
            self.retry_count < self.max_retries and
            self.booking.status == 'pending'
        )

    @property
    def total_fees(self):
        """Total fees (gateway + platform)"""
        return self.gateway_fee + self.platform_fee

    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        if self.expires_at and self.status == 'pending':
            return timezone.now() > self.expires_at
        return False

    def mark_completed(self, gateway_transaction_id=None, gateway_response=None):
        """Mark payment as completed"""
        if self.status in ['pending', 'processing']:
            self.status = 'completed'
            self.payment_date = timezone.now()
            
            if gateway_transaction_id:
                self.gateway_transaction_id = gateway_transaction_id
            
            if gateway_response:
                self.gateway_response = gateway_response
                self.gateway_callback_received = True
            
            self.save(update_fields=[
                'status', 'payment_date', 'gateway_transaction_id', 
                'gateway_response', 'gateway_callback_received'
            ])
            
            # Mark booking as paid
            self.booking.mark_as_paid()
            return True
        return False

    def mark_failed(self, failure_reason="", failure_code=""):
        """Mark payment as failed"""
        if self.status in ['pending', 'processing']:
            self.status = 'failed'
            self.failure_reason = failure_reason
            self.failure_code = failure_code
            self.save(update_fields=['status', 'failure_reason', 'failure_code'])
            return True
        return False

    def retry_payment(self):
        """Retry a failed payment"""
        if self.can_retry:
            self.status = 'pending'
            self.retry_count += 1
            self.last_retry_at = timezone.now()
            self.failure_reason = ""
            self.failure_code = ""
            self.save(update_fields=[
                'status', 'retry_count', 'last_retry_at', 
                'failure_reason', 'failure_code'
            ])
            return True
        return False

    def process_refund(self, refund_amount=None, reason=""):
        """Process a refund for this payment"""
        if self.status == 'completed':
            refund_amount = refund_amount or self.amount
            
            refund = Refund.objects.create(
                original_payment=self,
                refund_amount=refund_amount,
                reason=reason,
                currency=self.currency,
                refunded_to_user=self.user,
            )
            
            return refund
        return None

    def calculate_settlement_amount(self):
        """Calculate amount to settle to organizer"""
        # Deduct platform commission and fees
        commission_rate = Decimal('0.05')  # 5% commission
        commission_amount = self.amount * commission_rate
        settlement_amount = self.amount - commission_amount - self.total_fees
        return max(Decimal('0.00'), settlement_amount)

    def settle_to_organizer(self):
        """Mark as settled and create settlement record"""
        if self.status == 'completed' and not self.is_settled:
            self.settled_amount = self.calculate_settlement_amount()
            self.is_settled = True
            self.settlement_date = timezone.now()
            self.settlement_reference = f"SETTLE-{self.transaction_reference}"
            
            self.save(update_fields=[
                'settled_amount', 'is_settled', 'settlement_date', 'settlement_reference'
            ])
            
            # Create settlement record
            Settlement.objects.create(
                payment=self,
                organizer=self.booking.event.organizer,
                amount=self.settled_amount,
                currency=self.currency,
                reference=self.settlement_reference,
            )
            return True
        return False

    def save(self, *args, **kwargs):
        # Calculate net amount
        if not self.net_amount:
            self.net_amount = self.amount - self.total_fees
        
        # Set expiration if not set
        if not self.expires_at and self.status == 'pending':
            self.expires_at = timezone.now() + timezone.timedelta(minutes=30)
        
        super().save(*args, **kwargs)


class Refund(models.Model):
    """Refund transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    REFUND_TYPES = [
        ('full', 'Full Refund'),
        ('partial', 'Partial Refund'),
        ('service_fee', 'Service Fee Refund'),
        ('cancellation', 'Event Cancellation'),
        ('dispute', 'Dispute Resolution'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refund_reference = models.CharField(max_length=20, unique=True)
    original_payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    ticket = models.ForeignKey('tickets.Ticket', on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds')
    
    # Refund details
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    refund_type = models.CharField(max_length=20, choices=REFUND_TYPES, default='full')
    reason = models.TextField()
    
    # Processing information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Recipients
    refunded_to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_refunds')
    refund_method = models.CharField(max_length=50, blank=True, help_text="Method used for refund")
    refund_destination = models.CharField(max_length=200, blank=True, help_text="Account/phone number for refund")
    
    # Gateway processing
    gateway_refund_id = models.CharField(max_length=200, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    gateway_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Approval workflow
    requires_approval = models.BooleanField(default=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_refunds')
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Processing dates
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    customer_notified = models.BooleanField(default=False)
    organizer_notified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'refunds'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['refund_reference']),
            models.Index(fields=['original_payment']),
            models.Index(fields=['status']),
            models.Index(fields=['refunded_to_user']),
        ]

    def __str__(self):
        return f"Refund {self.refund_reference} - {self.refund_amount} {self.currency}"

    @property
    def is_approved(self):
        """Check if refund is approved"""
        return self.approved_at is not None

    @property
    def is_completed(self):
        """Check if refund is completed"""
        return self.status == 'completed'

    def approve(self, approved_by, notes=""):
        """Approve the refund"""
        if not self.is_approved and self.status == 'pending':
            self.approved_by = approved_by
            self.approved_at = timezone.now()
            self.approval_notes = notes
            self.status = 'processing'
            
            self.save(update_fields=[
                'approved_by', 'approved_at', 'approval_notes', 'status'
            ])
            return True
        return False

    def complete_refund(self, gateway_refund_id=None):
        """Mark refund as completed"""
        if self.status == 'processing':
            self.status = 'completed'
            self.completed_at = timezone.now()
            
            if gateway_refund_id:
                self.gateway_refund_id = gateway_refund_id
            
            self.save(update_fields=['status', 'completed_at', 'gateway_refund_id'])
            
            # Update original payment status
            if self.original_payment.amount <= self.refund_amount:
                self.original_payment.status = 'refunded'
            else:
                self.original_payment.status = 'partially_refunded'
            
            self.original_payment.save(update_fields=['status'])
            return True
        return False

    def save(self, *args, **kwargs):
        # Generate refund reference
        if not self.refund_reference:
            self.refund_reference = f"REF{generate_transaction_reference()[3:]}"
        
        # Calculate net refund amount
        if not self.net_refund_amount:
            self.net_refund_amount = self.refund_amount - self.processing_fee - self.gateway_fee
        
        super().save(*args, **kwargs)


class DiscountCode(models.Model):
    """Discount/promo codes for events"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('free_shipping', 'Free Service Fee'),
        ('buy_one_get_one', 'Buy One Get One'),
    ]
    
    USAGE_TYPES = [
        ('unlimited', 'Unlimited'),
        ('limited', 'Limited Uses'),
        ('single_use', 'Single Use Per Customer'),
        ('one_time', 'One Time Use Only'),
    ]
    
    # Basic information
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200, help_text="Internal name for the discount")
    description = models.TextField(blank=True)
    
    # Applicability
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True, related_name='discount_codes')
    applicable_ticket_types = models.ManyToManyField('tickets.TicketType', blank=True, related_name='discount_codes')
    is_global = models.BooleanField(default=False, help_text="Applies to all events")
    
    # Discount configuration
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage or fixed amount")
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum discount for percentage types")
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum order value")
    currency = models.CharField(max_length=3, default='UGX')
    
    # Usage limits
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPES, default='unlimited')
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total usage limit")
    usage_limit_per_user = models.PositiveIntegerField(default=1, help_text="Usage limit per user")
    times_used = models.PositiveIntegerField(default=0)
    
    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Target audience
    is_public = models.BooleanField(default=True, help_text="Publicly visible or requires code entry")
    target_user_groups = models.ManyToManyField('auth.Group', blank=True, help_text="Specific user groups eligible")
    first_time_buyers_only = models.BooleanField(default=False)
    
    # Creation and management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_discount_codes')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'discount_codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['event']),
            models.Index(fields=['valid_from', 'valid_until']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def is_valid(self):
        """Check if discount code is currently valid"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            not self.is_usage_limit_reached
        )

    @property
    def is_usage_limit_reached(self):
        """Check if usage limit is reached"""
        if self.usage_type == 'unlimited':
            return False
        return self.usage_limit and self.times_used >= self.usage_limit

    @property
    def remaining_uses(self):
        """Get remaining uses"""
        if self.usage_type == 'unlimited' or not self.usage_limit:
            return None
        return max(0, self.usage_limit - self.times_used)

    def is_valid_for_user(self, user):
        """Check if code is valid for specific user"""
        if not self.is_valid:
            return False
        
        # Check first-time buyer requirement
        if self.first_time_buyers_only:
            if user.bookings.filter(status='paid').exists():
                return False
        
        # Check user group restrictions
        if self.target_user_groups.exists():
            if not user.groups.filter(id__in=self.target_user_groups.all()).exists():
                return False
        
        # Check per-user usage limit
        user_usage_count = self.bookings.filter(user=user).count()
        if user_usage_count >= self.usage_limit_per_user:
            return False
        
        return True

    def is_valid_for_booking(self, booking):
        """Check if code is valid for specific booking"""
        if not self.is_valid_for_user(booking.user):
            return False
        
        # Check minimum order amount
        if booking.subtotal < self.min_order_amount:
            return False
        
        # Check event applicability
        if not self.is_global and self.event and self.event != booking.event:
            return False
        
        # Check ticket type applicability
        if self.applicable_ticket_types.exists():
            booking_ticket_types = [item.ticket_type for item in booking.items.all()]
            if not any(tt in self.applicable_ticket_types.all() for tt in booking_ticket_types):
                return False
        
        return True

    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order"""
        if self.discount_type == 'percentage':
            discount = (order_amount * self.discount_value) / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
        
        elif self.discount_type == 'fixed_amount':
            return min(self.discount_value, order_amount)
        
        elif self.discount_type == 'free_shipping':
            # This would be handled in the booking calculation
            return Decimal('0.00')
        
        return Decimal('0.00')

    def increment_usage(self):
        """Increment usage count"""
        self.times_used += 1
        self.save(update_fields=['times_used'])

    @classmethod
    def get_valid_codes_for_event(cls, event, user=None):
        """Get all valid discount codes for an event"""
        now = timezone.now()
        codes = cls.objects.filter(
            models.Q(is_global=True) | models.Q(event=event),
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        )
        
        if user:
            codes = [code for code in codes if code.is_valid_for_user(user)]
        
        return codes


class Settlement(models.Model):
    """Settlement records for organizers"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('disputed', 'Disputed'),
    ]
    
    SETTLEMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('paypal', 'PayPal'),
        ('stripe_connect', 'Stripe Connect'),
        ('manual', 'Manual Settlement'),
    ]
    
    # Basic information
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='settlements')
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settlements')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UGX')
    reference = models.CharField(max_length=200, unique=True)
    
    # Settlement details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    settlement_method = models.CharField(max_length=30, choices=SETTLEMENT_METHODS, default='bank_transfer')
    settlement_account = models.CharField(max_length=200, blank=True, help_text="Account number or phone")
    settlement_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_settlement_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Processing information
    gateway_settlement_id = models.CharField(max_length=200, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_settlements')
    
    # Dates
    settlement_date = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'settlements'
        ordering = ['-created_at']

    def __str__(self):
        return f"Settlement {self.reference} - {self.amount} {self.currency}"

    def complete_settlement(self, processed_by=None):
        """Mark settlement as completed"""
        if self.status in ['pending', 'processing']:
            self.status = 'completed'
            self.processed_at = timezone.now()
            self.processed_by = processed_by
            self.save(update_fields=['status', 'processed_at', 'processed_by'])
            return True
        return False

    def save(self, *args, **kwargs):
        if not self.net_settlement_amount:
            self.net_settlement_amount = self.amount - self.settlement_fee
        super().save(*args, **kwargs)


class PaymentAttempt(models.Model):
    """Track payment attempts for analytics and debugging"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='attempts')
    attempt_number = models.PositiveIntegerField()
    gateway_used = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50)
    amount_attempted = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Result
    was_successful = models.BooleanField(default=False)
    error_code = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_attempts'
        ordering = ['-created_at']
        unique_together = ['payment', 'attempt_number']

    def __str__(self):
        return f"Payment Attempt #{self.attempt_number} for {self.payment.transaction_reference}"

    def mark_completed(self, success=False, error_code="", error_message=""):
        """Mark attempt as completed"""
        self.completed_at = timezone.now()
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = Decimal(str(duration.total_seconds()))
        
        self.was_successful = success
        self.error_code = error_code
        self.error_message = error_message
        
        self.save(update_fields=[
            'completed_at', 'duration_seconds', 'was_successful', 
            'error_code', 'error_message'
        ])