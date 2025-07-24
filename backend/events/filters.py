import django_filters
from django.utils import timezone
from .models import Event, Category, Venue


class EventFilter(django_filters.FilterSet):
    # Date filters
    start_date_after = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    start_date_before = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='lte')
    date_range = django_filters.ChoiceFilter(
        method='filter_by_date_range',
        choices=[
            ('today', 'Today'),
            ('tomorrow', 'Tomorrow'),
            ('this_week', 'This Week'),
            ('this_weekend', 'This Weekend'),
            ('next_week', 'Next Week'),
            ('this_month', 'This Month'),
            ('next_month', 'Next Month'),
        ]
    )
    
    # Location filters
    city = django_filters.CharFilter(field_name='venue__city', lookup_expr='icontains')
    venue = django_filters.ModelChoiceFilter(queryset=Venue.objects.filter(is_active=True))
    
    # Category and type filters
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.filter(is_active=True))
    event_type = django_filters.ChoiceFilter(choices=Event.EVENT_TYPES)
    
    # Price filters
    is_free = django_filters.BooleanFilter()
    price_min = django_filters.NumberFilter(method='filter_by_min_price')
    price_max = django_filters.NumberFilter(method='filter_by_max_price')
    
    # Event characteristics
    age_restriction = django_filters.ChoiceFilter(choices=Event.AGE_RESTRICTIONS)
    crowd_level = django_filters.ChoiceFilter(
        field_name='expected_crowd_level',
        choices=Event.CROWD_LEVELS
    )
    
    # Status filters
    is_featured = django_filters.BooleanFilter()
    is_trending = django_filters.BooleanFilter()
    is_verified = django_filters.BooleanFilter()
    
    # Online/offline
    is_online = django_filters.BooleanFilter()
    
    class Meta:
        model = Event
        fields = [
            'category', 'event_type', 'venue', 'is_free', 'is_featured',
            'is_trending', 'is_verified', 'is_online', 'age_restriction'
        ]
    
    def filter_by_date_range(self, queryset, name, value):
        """Filter events by predefined date ranges"""
        now = timezone.now()
        
        if value == 'today':
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return queryset.filter(start_date__range=[start_of_day, end_of_day])
        
        elif value == 'tomorrow':
            tomorrow = now + timezone.timedelta(days=1)
            start_of_day = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
            return queryset.filter(start_date__range=[start_of_day, end_of_day])
        
        elif value == 'this_week':
            # Start of current week (Monday)
            days_since_monday = now.weekday()
            start_of_week = now - timezone.timedelta(days=days_since_monday)
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_week = start_of_week + timezone.timedelta(days=6, hours=23, minutes=59, seconds=59)
            return queryset.filter(start_date__range=[start_of_week, end_of_week])
        
        elif value == 'this_weekend':
            # Saturday and Sunday of current week
            days_since_monday = now.weekday()
            days_to_saturday = 5 - days_since_monday  # Saturday is day 5
            if days_to_saturday < 0:
                days_to_saturday += 7  # Next Saturday
            
            saturday = now + timezone.timedelta(days=days_to_saturday)
            start_of_saturday = saturday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_sunday = start_of_saturday + timezone.timedelta(days=1, hours=23, minutes=59, seconds=59)
            return queryset.filter(start_date__range=[start_of_saturday, end_of_sunday])
        
        elif value == 'next_week':
            # Next Monday to Sunday
            days_since_monday = now.weekday()
            days_to_next_monday = 7 - days_since_monday
            next_monday = now + timezone.timedelta(days=days_to_next_monday)
            start_of_next_week = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_next_week = start_of_next_week + timezone.timedelta(days=6, hours=23, minutes=59, seconds=59)
            return queryset.filter(start_date__range=[start_of_next_week, end_of_next_week])
        
        elif value == 'this_month':
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get last day of current month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            end_of_month = next_month - timezone.timedelta(microseconds=1)
            return queryset.filter(start_date__range=[start_of_month, end_of_month])
        
        elif value == 'next_month':
            # Get first day of next month
            if now.month == 12:
                start_of_next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                end_of_next_month = now.replace(year=now.year + 1, month=2, day=1) - timezone.timedelta(microseconds=1)
            else:
                start_of_next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                if now.month == 11:  # November, next month is December
                    end_of_next_month = now.replace(year=now.year + 1, month=1, day=1) - timezone.timedelta(microseconds=1)
                else:
                    end_of_next_month = now.replace(month=now.month + 2, day=1) - timezone.timedelta(microseconds=1)
            return queryset.filter(start_date__range=[start_of_next_month, end_of_next_month])
        
        return queryset
    
    def filter_by_min_price(self, queryset, name, value):
        """Filter events with minimum ticket price"""
        # This would require joining with ticket types
        # For now, we'll return the queryset as-is
        # TODO: Implement proper price filtering with ticket types
        return queryset
    
    def filter_by_max_price(self, queryset, name, value):
        """Filter events with maximum ticket price"""
        # This would require joining with ticket types
        # For now, we'll return the queryset as-is
        # TODO: Implement proper price filtering with ticket types
        return queryset