from rest_framework import serializers
from django.utils import timezone
from .models import (
    Category, Venue, VenueAmenity, SeatingPlan, Event, 
    EventTag, EventTagging, EventImage
)
from users.serializers import UserProfileSerializer


class CategorySerializer(serializers.ModelSerializer):
    event_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color', 
            'is_active', 'event_count', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']
    
    def get_event_count(self, obj):
        return obj.events.filter(status='published').count()


class VenueAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VenueAmenity
        fields = [
            'id', 'amenity_type', 'name', 'description', 'is_included',
            'additional_cost', 'currency', 'is_available'
        ]


class SeatingPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatingPlan
        fields = [
            'id', 'name', 'seating_type', 'description', 'capacity',
            'layout_image', 'seating_map', 'base_price', 'currency', 'is_active'
        ]


class VenueDetailSerializer(serializers.ModelSerializer):
    amenities = VenueAmenitySerializer(many=True, read_only=True)
    seating_plans = SeatingPlanSerializer(many=True, read_only=True)
    upcoming_events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Venue
        fields = [
            'id', 'name', 'slug', 'venue_type', 'description', 'address',
            'city', 'state_region', 'country', 'postal_code', 'latitude', 'longitude',
            'phone', 'email', 'website', 'total_capacity', 'parking_available',
            'parking_capacity', 'accessibility_features', 'main_image', 'gallery_images',
            'manager_name', 'manager_contact', 'is_verified', 'is_active',
            'amenities', 'seating_plans', 'upcoming_events_count', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at', 'upcoming_events_count']
    
    def get_upcoming_events_count(self, obj):
        return obj.events.filter(
            status='published',
            start_date__gt=timezone.now()
        ).count()


class VenueListSerializer(serializers.ModelSerializer):
    upcoming_events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Venue
        fields = [
            'id', 'name', 'slug', 'venue_type', 'city', 'country',
            'total_capacity', 'main_image', 'is_verified', 'upcoming_events_count'
        ]
    
    def get_upcoming_events_count(self, obj):
        return obj.events.filter(
            status='published',
            start_date__gt=timezone.now()
        ).count()


class EventTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'image', 'caption', 'is_primary', 'order']


class EventListSerializer(serializers.ModelSerializer):
    organizer = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    venue_name = serializers.CharField(source='venue.name', read_only=True)
    venue_city = serializers.CharField(source='venue.city', read_only=True)
    tags = EventTagSerializer(source='taggings.tag', many=True, read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()
    tickets_available = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'short_description', 'organizer', 'category',
            'event_type', 'venue_name', 'venue_city', 'is_online', 'start_date',
            'end_date', 'banner_image', 'is_free', 'status', 'is_featured',
            'is_verified', 'is_trending', 'view_count', 'like_count', 'tags',
            'is_upcoming', 'is_sold_out', 'tickets_available', 'created_at'
        ]


class EventDetailSerializer(serializers.ModelSerializer):
    organizer = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    venue = VenueDetailSerializer(read_only=True)
    tags = EventTagSerializer(source='taggings.tag', many=True, read_only=True)
    images = EventImageSerializer(many=True, read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    is_sold_out = serializers.ReadOnlyField()
    tickets_available = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'organizer', 'category', 'event_type', 'venue', 'is_online', 'online_link',
            'start_date', 'end_date', 'timezone_info', 'doors_open',
            'banner_image', 'gallery_images', 'video_url', 'is_free',
            'ticket_sales_start', 'ticket_sales_end', 'max_tickets_per_order',
            'expected_crowd_level', 'age_restriction', 'dress_code',
            'refund_policy', 'terms_and_conditions', 'special_instructions',
            'facebook_event_url', 'twitter_hashtag', 'instagram_handle',
            'status', 'is_featured', 'is_verified', 'is_trending',
            'view_count', 'like_count', 'share_count', 'tags', 'images',
            'is_upcoming', 'is_ongoing', 'is_past', 'is_sold_out', 'tickets_available',
            'created_at', 'updated_at', 'published_at'
        ]


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'short_description', 'category', 'event_type',
            'venue', 'is_online', 'online_link', 'start_date', 'end_date',
            'timezone_info', 'doors_open', 'banner_image', 'gallery_images',
            'video_url', 'is_free', 'ticket_sales_start', 'ticket_sales_end',
            'max_tickets_per_order', 'expected_crowd_level', 'age_restriction',
            'dress_code', 'refund_policy', 'terms_and_conditions',
            'special_instructions', 'facebook_event_url', 'twitter_hashtag',
            'instagram_handle', 'tags'
        ]
    
    def validate(self, attrs):
        if attrs.get('start_date') and attrs.get('end_date'):
            if attrs['start_date'] >= attrs['end_date']:
                raise serializers.ValidationError(
                    "End date must be after start date."
                )
        
        if attrs.get('ticket_sales_start') and attrs.get('ticket_sales_end'):
            if attrs['ticket_sales_start'] >= attrs['ticket_sales_end']:
                raise serializers.ValidationError(
                    "Ticket sales end date must be after start date."
                )
        
        return attrs
    
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        event = Event.objects.create(**validated_data)
        
        # Handle tags
        for tag_name in tags_data:
            tag, created = EventTag.objects.get_or_create(
                name=tag_name,
                defaults={'slug': tag_name.lower().replace(' ', '-')}
            )
            EventTagging.objects.create(event=event, tag=tag)
        
        return event
    
    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        
        # Update event fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tags_data is not None:
            instance.taggings.all().delete()
            for tag_name in tags_data:
                tag, created = EventTag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': tag_name.lower().replace(' ', '-')}
                )
                EventTagging.objects.create(event=instance, tag=tag)
        
        return instance


class AdminEventListSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.full_name', read_only=True)
    organizer_email = serializers.CharField(source='organizer.email', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    venue_name = serializers.CharField(source='venue.name', read_only=True)
    venue_city = serializers.CharField(source='venue.city', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'organizer_name', 'organizer_email',
            'category_name', 'venue_name', 'venue_city', 'event_type',
            'start_date', 'end_date', 'status', 'is_featured', 'is_verified',
            'view_count', 'created_at', 'published_at'
        ]


class EventApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['status', 'is_verified']
    
    def validate_status(self, value):
        if value not in ['published', 'cancelled']:
            raise serializers.ValidationError(
                "Status can only be changed to 'published' or 'cancelled' for approval."
            )
        return value