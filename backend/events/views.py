from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.text import slugify
import logging

from .models import (
    Category, Venue, VenueAmenity, SeatingPlan, Event, 
    EventTag, EventTagging, EventImage
)
from .serializers import (
    CategorySerializer, VenueListSerializer, VenueDetailSerializer,
    EventListSerializer, EventDetailSerializer, EventCreateUpdateSerializer,
    AdminEventListSerializer, EventApprovalSerializer, EventTagSerializer
)
from .filters import EventFilter
from .permissions import IsOrganizerOrReadOnly, IsOwnerOrReadOnly

logger = logging.getLogger(__name__)


# Category Views
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True).order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


# Venue Views
class VenueListView(generics.ListAPIView):
    queryset = Venue.objects.filter(is_active=True).order_by('name')
    serializer_class = VenueListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['venue_type', 'city', 'is_verified']
    search_fields = ['name', 'description', 'address', 'city']
    ordering_fields = ['name', 'total_capacity', 'created_at']


class VenueDetailView(generics.RetrieveAPIView):
    queryset = Venue.objects.filter(is_active=True)
    serializer_class = VenueDetailSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


# Event Views
class EventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['title', 'description', 'venue__name', 'venue__city']
    ordering_fields = ['start_date', 'created_at', 'view_count', 'like_count']
    ordering = ['start_date']
    
    def get_queryset(self):
        queryset = Event.objects.filter(status='published').select_related(
            'organizer', 'category', 'venue'
        ).prefetch_related('taggings__tag')
        
        # Filter by upcoming events by default
        if not self.request.query_params.get('include_past'):
            queryset = queryset.filter(start_date__gt=timezone.now())
        
        return queryset


class EventDetailView(generics.RetrieveAPIView):
    queryset = Event.objects.filter(status='published').select_related(
        'organizer', 'category', 'venue'
    ).prefetch_related('taggings__tag', 'images')
    serializer_class = EventDetailSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class EventCreateView(generics.CreateAPIView):
    serializer_class = EventCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Auto-generate slug
        title = serializer.validated_data['title']
        slug = slugify(title)
        
        # Ensure unique slug
        counter = 1
        original_slug = slug
        while Event.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        serializer.save(
            organizer=self.request.user,
            slug=slug,
            status='draft'  # New events start as draft
        )


class EventUpdateView(generics.UpdateAPIView):
    serializer_class = EventCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user)


class EventDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user)


class MyEventsView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'event_type', 'is_featured']
    ordering_fields = ['start_date', 'created_at', 'view_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Event.objects.filter(
            organizer=self.request.user
        ).select_related('category', 'venue').prefetch_related('taggings__tag')


# Featured and Trending Events
class FeaturedEventsView(generics.ListAPIView):
    queryset = Event.objects.filter(
        status='published',
        is_featured=True,
        start_date__gt=timezone.now()
    ).select_related('organizer', 'category', 'venue')[:10]
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]


class TrendingEventsView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Event.objects.filter(
            status='published',
            start_date__gt=timezone.now()
        ).select_related('organizer', 'category', 'venue').order_by(
            '-view_count', '-like_count'
        )[:20]


class NearbyEventsView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        city = self.request.query_params.get('city', 'Kampala')
        return Event.objects.filter(
            status='published',
            start_date__gt=timezone.now(),
            venue__city__icontains=city
        ).select_related('organizer', 'category', 'venue')[:20]


# Event Actions
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id, status='published')
        # Here you would implement actual like/unlike logic with user tracking
        event.like_count += 1
        event.save(update_fields=['like_count'])
        
        return Response({
            'message': 'Event liked successfully.',
            'like_count': event.like_count
        })
    except Event.DoesNotExist:
        return Response(
            {'error': 'Event not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def share_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id, status='published')
        event.share_count += 1
        event.save(update_fields=['share_count'])
        
        return Response({
            'message': 'Event shared successfully.',
            'share_count': event.share_count
        })
    except Event.DoesNotExist:
        return Response(
            {'error': 'Event not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsOwnerOrReadOnly])
def publish_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id, organizer=request.user)
        
        if event.status != 'draft':
            return Response(
                {'error': 'Only draft events can be published.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event.status = 'published'
        event.published_at = timezone.now()
        event.save(update_fields=['status', 'published_at'])
        
        return Response({
            'message': 'Event published successfully and is now awaiting admin approval.',
            'status': event.status
        })
    except Event.DoesNotExist:
        return Response(
            {'error': 'Event not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


# Tag Views
class TagListView(generics.ListAPIView):
    queryset = EventTag.objects.all().order_by('name')
    serializer_class = EventTagSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


# Search View
class EventSearchView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        location = self.request.query_params.get('location', '')
        category = self.request.query_params.get('category', '')
        
        queryset = Event.objects.filter(status='published')
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(venue__name__icontains=query) |
                Q(taggings__tag__name__icontains=query)
            ).distinct()
        
        if location:
            queryset = queryset.filter(venue__city__icontains=location)
        
        if category:
            queryset = queryset.filter(category__slug=category)
        
        return queryset.select_related('organizer', 'category', 'venue')


# Admin Views
class AdminEventListView(generics.ListAPIView):
    queryset = Event.objects.all().select_related(
        'organizer', 'category', 'venue'
    ).order_by('-created_at')
    serializer_class = AdminEventListSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_verified', 'is_featured', 'event_type', 'category']
    search_fields = ['title', 'organizer__email', 'venue__name']
    ordering_fields = ['created_at', 'start_date', 'view_count']


class AdminEventDetailView(generics.RetrieveAPIView):
    queryset = Event.objects.all().select_related('organizer', 'category', 'venue')
    serializer_class = EventDetailSerializer
    permission_classes = [permissions.IsAdminUser]


@api_view(['PATCH'])
@permission_classes([permissions.IsAdminUser])
def approve_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        serializer = EventApprovalSerializer(event, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            
            action = 'approved' if event.status == 'published' else 'rejected'
            return Response({
                'message': f'Event {action} successfully.',
                'status': event.status,
                'is_verified': event.is_verified
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Event.DoesNotExist:
        return Response(
            {'error': 'Event not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def toggle_event_featured(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        event.is_featured = not event.is_featured
        event.save(update_fields=['is_featured'])
        
        return Response({
            'message': f'Event {"featured" if event.is_featured else "unfeatured"} successfully.',
            'is_featured': event.is_featured
        })
    except Event.DoesNotExist:
        return Response(
            {'error': 'Event not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


# Analytics Views
class EventAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user_events = Event.objects.filter(organizer=request.user)
        
        analytics = {
            'total_events': user_events.count(),
            'published_events': user_events.filter(status='published').count(),
            'draft_events': user_events.filter(status='draft').count(),
            'upcoming_events': user_events.filter(
                status='published',
                start_date__gt=timezone.now()
            ).count(),
            'past_events': user_events.filter(
                end_date__lt=timezone.now()
            ).count(),
            'total_views': user_events.aggregate(
                total=Count('view_count')
            )['total'] or 0,
            'total_likes': user_events.aggregate(
                total=Count('like_count')
            )['total'] or 0,
        }
        
        return Response(analytics)
