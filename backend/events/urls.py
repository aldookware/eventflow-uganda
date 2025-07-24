from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'events'

# API URLs
urlpatterns = [
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Venues
    path('venues/', views.VenueListView.as_view(), name='venue-list'),
    path('venues/<slug:slug>/', views.VenueDetailView.as_view(), name='venue-detail'),
    
    # Events
    path('', views.EventListView.as_view(), name='event-list'),
    path('create/', views.EventCreateView.as_view(), name='event-create'),
    path('search/', views.EventSearchView.as_view(), name='event-search'),
    path('featured/', views.FeaturedEventsView.as_view(), name='featured-events'),
    path('trending/', views.TrendingEventsView.as_view(), name='trending-events'),
    path('nearby/', views.NearbyEventsView.as_view(), name='nearby-events'),
    path('my-events/', views.MyEventsView.as_view(), name='my-events'),
    path('analytics/', views.EventAnalyticsView.as_view(), name='event-analytics'),
    
    # Event detail and actions
    path('<slug:slug>/', views.EventDetailView.as_view(), name='event-detail'),
    path('<slug:slug>/edit/', views.EventUpdateView.as_view(), name='event-update'),
    path('<slug:slug>/delete/', views.EventDeleteView.as_view(), name='event-delete'),
    
    # Event actions
    path('<uuid:event_id>/like/', views.like_event, name='like-event'),
    path('<uuid:event_id>/share/', views.share_event, name='share-event'),
    path('<uuid:event_id>/publish/', views.publish_event, name='publish-event'),
    
    # Tags
    path('tags/', views.TagListView.as_view(), name='tag-list'),
    
    # Admin URLs
    path('admin/events/', views.AdminEventListView.as_view(), name='admin-event-list'),
    path('admin/events/<uuid:pk>/', views.AdminEventDetailView.as_view(), name='admin-event-detail'),
    path('admin/events/<uuid:event_id>/approve/', views.approve_event, name='approve-event'),
    path('admin/events/<uuid:event_id>/toggle-featured/', views.toggle_event_featured, name='toggle-event-featured'),
]