from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import uuid

User = get_user_model()


class Category(models.Model):
    """Event categories for organizing events"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    color = models.CharField(max_length=7, default="#000000", help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'event_categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Venue(models.Model):
    """Physical venues where events take place"""
    VENUE_TYPES = [
        ('concert_hall', 'Concert Hall'),
        ('stadium', 'Stadium'),
        ('theater', 'Theater'),
        ('conference_center', 'Conference Center'),
        ('club', 'Club'),
        ('outdoor', 'Outdoor'),
        ('hotel', 'Hotel'),
        ('restaurant', 'Restaurant'),
        ('school', 'School'),
        ('church', 'Church'),
        ('community_center', 'Community Center'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    venue_type = models.CharField(max_length=50, choices=VENUE_TYPES, default='other')
    description = models.TextField(blank=True)
    
    # Location details
    address = models.TextField()
    city = models.CharField(max_length=100)
    state_region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Uganda')
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Contact information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Capacity and features
    total_capacity = models.PositiveIntegerField(default=0)
    parking_available = models.BooleanField(default=False)
    parking_capacity = models.PositiveIntegerField(default=0, blank=True)
    accessibility_features = models.TextField(blank=True, help_text="Wheelchair access, elevators, etc.")
    
    # Media
    main_image = models.ImageField(upload_to='venues/', null=True, blank=True)
    gallery_images = models.JSONField(default=list, blank=True, help_text="List of image URLs")
    
    # Business details
    manager_name = models.CharField(max_length=200, blank=True)
    manager_contact = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'venues'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.city}"

    def get_absolute_url(self):
        return reverse('venue-detail', kwargs={'slug': self.slug})


class VenueAmenity(models.Model):
    """Amenities available at venues"""
    AMENITY_TYPES = [
        ('parking', 'Parking'),
        ('wifi', 'WiFi'),
        ('catering', 'Catering'),
        ('bar', 'Bar'),
        ('air_conditioning', 'Air Conditioning'),
        ('sound_system', 'Sound System'),
        ('lighting', 'Professional Lighting'),
        ('stage', 'Stage'),
        ('dressing_room', 'Dressing Room'),
        ('security', 'Security'),
        ('medical', 'Medical Facilities'),
        ('accessibility', 'Wheelchair Accessible'),
        ('restrooms', 'Restrooms'),
        ('vip_area', 'VIP Area'),
        ('coat_check', 'Coat Check'),
    ]
    
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='amenities')
    amenity_type = models.CharField(max_length=50, choices=AMENITY_TYPES)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_included = models.BooleanField(default=True, help_text="Included in venue rental or extra charge")
    additional_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='UGX')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'venue_amenities'
        verbose_name_plural = 'Venue Amenities'
        unique_together = ['venue', 'amenity_type']

    def __str__(self):
        return f"{self.venue.name} - {self.name}"


class SeatingPlan(models.Model):
    """Seating arrangements for venues"""
    SEATING_TYPES = [
        ('general', 'General Admission'),
        ('reserved', 'Reserved Seating'),
        ('vip', 'VIP Section'),
        ('table', 'Table Seating'),
        ('standing', 'Standing Room'),
        ('box', 'Box Seats'),
        ('balcony', 'Balcony'),
        ('floor', 'Floor Seating'),
    ]
    
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='seating_plans')
    name = models.CharField(max_length=100)
    seating_type = models.CharField(max_length=20, choices=SEATING_TYPES)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField()
    layout_image = models.ImageField(upload_to='seating_plans/', null=True, blank=True)
    seating_map = models.JSONField(default=dict, blank=True, help_text="Detailed seating layout data")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='UGX')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'seating_plans'
        ordering = ['venue', 'name']

    def __str__(self):
        return f"{self.venue.name} - {self.name} ({self.capacity} seats)"


class Event(models.Model):
    """Main event model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
        ('completed', 'Completed'),
    ]
    
    EVENT_TYPES = [
        ('concert', 'Concert'),
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('festival', 'Festival'),
        ('sports', 'Sports'),
        ('theater', 'Theater'),
        ('comedy', 'Comedy'),
        ('exhibition', 'Exhibition'),
        ('networking', 'Networking'),
        ('charity', 'Charity'),
        ('religious', 'Religious'),
        ('cultural', 'Cultural'),
        ('educational', 'Educational'),
        ('business', 'Business'),
        ('social', 'Social'),
        ('other', 'Other'),
    ]
    
    CROWD_LEVELS = [
        ('low', 'Low - Intimate gathering'),
        ('medium', 'Medium - Moderate crowd'),
        ('high', 'High - Large crowd'),
        ('very_high', 'Very High - Massive crowd'),
    ]
    
    AGE_RESTRICTIONS = [
        ('all_ages', 'All Ages'),
        ('13+', '13+'),
        ('16+', '16+'),
        ('18+', '18+'),
        ('21+', '21+'),
    ]
    
    # Basic information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    # Organizer and category
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    
    # Venue and location
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='events')
    is_online = models.BooleanField(default=False)
    online_link = models.URLField(blank=True)
    
    # Date and time
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    timezone_info = models.CharField(max_length=50, default='Africa/Kampala')
    doors_open = models.DateTimeField(null=True, blank=True)
    
    # Media
    banner_image = models.ImageField(upload_to='events/banners/', null=True, blank=True)
    gallery_images = models.JSONField(default=list, blank=True)
    video_url = models.URLField(blank=True)
    
    # Ticket information
    is_free = models.BooleanField(default=False)
    ticket_sales_start = models.DateTimeField(null=True, blank=True)
    ticket_sales_end = models.DateTimeField(null=True, blank=True)
    max_tickets_per_order = models.PositiveIntegerField(default=10)
    
    # Event characteristics
    expected_crowd_level = models.CharField(max_length=20, choices=CROWD_LEVELS, default='medium')
    age_restriction = models.CharField(max_length=20, choices=AGE_RESTRICTIONS, default='all_ages')
    dress_code = models.CharField(max_length=200, blank=True)
    
    # Policies and rules
    refund_policy = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Social and marketing
    facebook_event_url = models.URLField(blank=True)
    twitter_hashtag = models.CharField(max_length=100, blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    
    # Status and moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    
    # Metrics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'events'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['venue']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('event-detail', kwargs={'slug': self.slug})

    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def is_past(self):
        return self.end_date < timezone.now()

    @property
    def is_sold_out(self):
        total_tickets = sum(tt.quantity for tt in self.ticket_types.all())
        sold_tickets = sum(tt.sold_count for tt in self.ticket_types.all())
        return sold_tickets >= total_tickets if total_tickets > 0 else False

    @property
    def tickets_available(self):
        return self.ticket_sales_start <= timezone.now() <= self.ticket_sales_end if self.ticket_sales_start and self.ticket_sales_end else True

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class EventTag(models.Model):
    """Tags for events to improve searchability"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_tags'
        ordering = ['name']

    def __str__(self):
        return self.name


class EventTagging(models.Model):
    """Many-to-many relationship between events and tags"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='taggings')
    tag = models.ForeignKey(EventTag, on_delete=models.CASCADE, related_name='taggings')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_taggings'
        unique_together = ['event', 'tag']

    def __str__(self):
        return f"{self.event.title} - {self.tag.name}"


class EventImage(models.Model):
    """Additional images for events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'event_images'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.event.title} - Image {self.id}"