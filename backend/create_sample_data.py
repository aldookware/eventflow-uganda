#!/usr/bin/env python
"""
Sample data creation script for EventFlow/TicketRise platform
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventflow.settings')
django.setup()

from django.contrib.auth import get_user_model
from events.models import Category, Venue, Event, EventTag, EventTagging
from tickets.models import TicketType

User = get_user_model()

def create_sample_data():
    print("Creating sample data for EventFlow platform...")
    
    # Create sample users (organizers)
    organizers = []
    organizer_data = [
        {
            'email': 'music.events@eventflow.ug',
            'first_name': 'Sarah',
            'last_name': 'Namubiru',
            'role': 'organizer',
            'city': 'Kampala',
            'phone': '+256700123456'
        },
        {
            'email': 'tech.events@eventflow.ug', 
            'first_name': 'David',
            'last_name': 'Mukasa',
            'role': 'organizer',
            'city': 'Entebbe',
            'phone': '+256700234567'
        },
        {
            'email': 'sports.events@eventflow.ug',
            'first_name': 'Grace',
            'last_name': 'Akello',
            'role': 'organizer',
            'city': 'Jinja',
            'phone': '+256700345678'
        }
    ]
    
    for data in organizer_data:
        user, created = User.objects.get_or_create(
            email=data['email'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': data['role'],
                'city': data['city'],
                'phone': data['phone'],
                'is_verified': True,
                'email_verified': True,
                'phone_verified': True
            }
        )
        user.set_password('organizer123')
        user.save()
        organizers.append(user)
        print(f"Created organizer: {user.full_name}")
    
    # Create regular users
    users_data = [
        {
            'email': 'john.doe@gmail.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'city': 'Kampala',
            'phone': '+256700111222'
        },
        {
            'email': 'jane.smith@gmail.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'city': 'Entebbe',
            'phone': '+256700333444'
        }
    ]
    
    for data in users_data:
        user, created = User.objects.get_or_create(
            email=data['email'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'city': data['city'],
                'phone': data['phone'],
                'is_verified': True,
                'email_verified': True,
                'phone_verified': True
            }
        )
        user.set_password('user123')
        user.save()
        print(f"Created user: {user.full_name}")
    
    # Create event categories
    categories_data = [
        {'name': 'Music & Concerts', 'slug': 'music-concerts', 'description': 'Live music performances and concerts'},
        {'name': 'Technology', 'slug': 'technology', 'description': 'Tech conferences, workshops and meetups'},
        {'name': 'Sports & Fitness', 'slug': 'sports-fitness', 'description': 'Sports events and fitness activities'},
        {'name': 'Business & Networking', 'slug': 'business-networking', 'description': 'Business conferences and networking events'},
        {'name': 'Arts & Culture', 'slug': 'arts-culture', 'description': 'Art exhibitions, cultural events and festivals'},
        {'name': 'Food & Drink', 'slug': 'food-drink', 'description': 'Food festivals and culinary events'},
    ]
    
    categories = []
    for data in categories_data:
        category, created = Category.objects.get_or_create(
            slug=data['slug'],
            defaults={
                'name': data['name'],
                'description': data['description'],
                'is_active': True
            }
        )
        categories.append(category)
        print(f"Created category: {category.name}")
    
    # Create venues
    venues_data = [
        {
            'name': 'Serena Conference Centre',
            'slug': 'serena-conference-centre',
            'description': 'Premier conference and event venue in the heart of Kampala',
            'address': 'Nile Avenue, Kampala',
            'city': 'Kampala',
            'country': 'Uganda',
            'total_capacity': 500,
            'latitude': 0.3136,
            'longitude': 32.5811
        },
        {
            'name': 'Kampala Sports Club',
            'slug': 'kampala-sports-club',
            'description': 'Historic sports and social club',
            'address': 'Lugogo, Kampala',
            'city': 'Kampala', 
            'country': 'Uganda',
            'total_capacity': 1000,
            'latitude': 0.3476,
            'longitude': 32.6052
        },
        {
            'name': 'Imperial Resort Beach Hotel',
            'slug': 'imperial-resort-beach',
            'description': 'Lakeside venue perfect for outdoor events',
            'address': 'Lake Victoria, Entebbe',
            'city': 'Entebbe',
            'country': 'Uganda', 
            'total_capacity': 300,
            'latitude': 0.0647,
            'longitude': 32.4656
        },
        {
            'name': 'Jinja Sailing Club',
            'slug': 'jinja-sailing-club',
            'description': 'Scenic venue by the Nile River',
            'address': 'Source of the Nile, Jinja',
            'city': 'Jinja',
            'country': 'Uganda',
            'total_capacity': 200,
            'latitude': 0.4241,
            'longitude': 33.2041
        }
    ]
    
    venues = []
    for data in venues_data:
        venue, created = Venue.objects.get_or_create(
            slug=data['slug'],
            defaults={
                'name': data['name'],
                'description': data['description'],
                'address': data['address'],
                'city': data['city'],
                'country': data['country'],
                'total_capacity': data['total_capacity'],
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'is_active': True
            }
        )
        venues.append(venue)
        print(f"Created venue: {venue.name}")
    
    # Create event tags
    tags_data = ['live-music', 'conference', 'workshop', 'networking', 'outdoor', 'tech', 'startup', 'wellness', 'cultural', 'family-friendly']
    tags = []
    for tag_name in tags_data:
        tag, created = EventTag.objects.get_or_create(
            name=tag_name,
            defaults={'slug': tag_name}
        )
        tags.append(tag)
        print(f"Created tag: {tag.name}")
    
    # Create sample events
    events_data = [
        {
            'title': 'Uganda Music Festival 2025',
            'slug': 'uganda-music-festival-2025',
            'description': 'The biggest music festival in East Africa featuring local and international artists. Experience the best of Ugandan music culture with traditional and contemporary performances.',
            'short_description': 'East Africa\'s biggest music festival with local and international artists',
            'organizer': organizers[0],
            'category': categories[0],  # Music & Concerts
            'venue': venues[1],  # Kampala Sports Club
            'event_type': 'festival',
            'start_date': timezone.now() + timedelta(days=30),
            'end_date': timezone.now() + timedelta(days=32),
            'status': 'published',
            'is_featured': True,
            'is_verified': True,
            'tags': ['live-music', 'cultural', 'outdoor']
        },
        {
            'title': 'Tech Innovation Summit Kampala',
            'slug': 'tech-innovation-summit-kampala',
            'description': 'Join leading tech innovators, entrepreneurs, and investors for a day of networking, learning, and collaboration. Discover the latest trends in African tech.',
            'short_description': 'Leading tech summit bringing together innovators and entrepreneurs',
            'organizer': organizers[1],
            'category': categories[1],  # Technology
            'venue': venues[0],  # Serena Conference Centre
            'event_type': 'conference',
            'start_date': timezone.now() + timedelta(days=15),
            'end_date': timezone.now() + timedelta(days=15),
            'status': 'published',
            'is_featured': True,
            'is_verified': True,
            'tags': ['tech', 'conference', 'startup', 'networking']
        },
        {
            'title': 'Lake Victoria Marathon',
            'slug': 'lake-victoria-marathon',
            'description': 'Run along the beautiful shores of Lake Victoria in this annual marathon event. Multiple race categories available for all fitness levels.',
            'short_description': 'Annual marathon along the shores of Lake Victoria',
            'organizer': organizers[2],
            'category': categories[2],  # Sports & Fitness
            'venue': venues[2],  # Imperial Resort Beach Hotel
            'event_type': 'sports',
            'start_date': timezone.now() + timedelta(days=45),
            'end_date': timezone.now() + timedelta(days=45),
            'status': 'published',
            'is_featured': False,
            'is_verified': True,
            'tags': ['outdoor', 'wellness', 'family-friendly']
        },
        {
            'title': 'African Business Leaders Forum',
            'slug': 'african-business-leaders-forum',
            'description': 'Network with top business leaders across Africa. Learn about investment opportunities, business growth strategies, and economic trends.',
            'short_description': 'Premier networking event for African business leaders',
            'organizer': organizers[1],
            'category': categories[3],  # Business & Networking  
            'venue': venues[0],  # Serena Conference Centre
            'event_type': 'conference',
            'start_date': timezone.now() + timedelta(days=60),
            'end_date': timezone.now() + timedelta(days=61),
            'status': 'published',
            'is_featured': False,
            'is_verified': True,
            'tags': ['networking', 'conference']
        },
        {
            'title': 'Jinja Cultural Arts Festival',
            'slug': 'jinja-cultural-arts-festival',
            'description': 'Celebrate Uganda\'s rich cultural heritage with traditional dances, crafts, and local cuisine by the source of the Nile.',
            'short_description': 'Cultural festival celebrating Uganda\'s heritage by the Nile',
            'organizer': organizers[0],
            'category': categories[4],  # Arts & Culture
            'venue': venues[3],  # Jinja Sailing Club
            'event_type': 'festival',
            'start_date': timezone.now() + timedelta(days=75),
            'end_date': timezone.now() + timedelta(days=77),
            'status': 'published',
            'is_featured': False,
            'is_verified': True,
            'tags': ['cultural', 'family-friendly', 'outdoor']
        },
        {
            'title': 'Future of Mobile Development Workshop',
            'slug': 'future-mobile-dev-workshop',
            'description': 'Hands-on workshop covering the latest in mobile app development including Flutter, React Native, and native development.',
            'short_description': 'Hands-on mobile development workshop with latest technologies',
            'organizer': organizers[1],
            'category': categories[1],  # Technology
            'venue': venues[0],  # Serena Conference Centre
            'event_type': 'workshop',
            'start_date': timezone.now() + timedelta(days=20),
            'end_date': timezone.now() + timedelta(days=20),
            'status': 'pending',
            'is_featured': False,
            'is_verified': False,
            'tags': ['tech', 'workshop']
        }
    ]
    
    events = []
    for data in events_data:
        event, created = Event.objects.get_or_create(
            slug=data['slug'],
            defaults={
                'title': data['title'],
                'description': data['description'],
                'short_description': data['short_description'],
                'organizer': data['organizer'],
                'category': data['category'],
                'venue': data['venue'],
                'event_type': data['event_type'],
                'start_date': data['start_date'],
                'end_date': data['end_date'],
                'status': data['status'],
                'is_featured': data['is_featured'],
                'is_verified': data['is_verified'],
            }
        )
        
        # Add tags to event
        for tag_name in data['tags']:
            tag = EventTag.objects.get(name=tag_name)
            EventTagging.objects.get_or_create(event=event, tag=tag)
        
        events.append(event)
        print(f"Created event: {event.title}")
    
    # Create ticket types for events
    ticket_types_data = [
        # Uganda Music Festival
        {
            'event': events[0],
            'tickets': [
                {'name': 'General Admission', 'price': '50000', 'quantity': 2000, 'description': 'General access to festival grounds'},
                {'name': 'VIP Pass', 'price': '150000', 'quantity': 200, 'description': 'VIP area access with premium amenities'},
                {'name': 'Early Bird', 'price': '35000', 'quantity': 500, 'description': 'Limited early bird pricing', 'sale_ends': timezone.now() + timedelta(days=10)},
            ]
        },
        # Tech Innovation Summit
        {
            'event': events[1],
            'tickets': [
                {'name': 'Standard Pass', 'price': '75000', 'quantity': 300, 'description': 'Full day access to all sessions'},
                {'name': 'Student Discount', 'price': '25000', 'quantity': 100, 'description': 'Discounted rate for students with valid ID'},
                {'name': 'Startup Package', 'price': '100000', 'quantity': 50, 'description': 'Includes networking lunch and startup exhibition'},
            ]
        },
        # Lake Victoria Marathon
        {
            'event': events[2],
            'tickets': [
                {'name': 'Full Marathon', 'price': '30000', 'quantity': 500, 'description': '42km full marathon registration'},
                {'name': 'Half Marathon', 'price': '20000', 'quantity': 800, 'description': '21km half marathon registration'},
                {'name': 'Fun Run (5km)', 'price': '10000', 'quantity': 1000, 'description': '5km family-friendly fun run'},
            ]
        },
        # Business Leaders Forum
        {
            'event': events[3],
            'tickets': [
                {'name': 'Conference Pass', 'price': '200000', 'quantity': 200, 'description': 'Two-day conference access'},
                {'name': 'Networking Dinner', 'price': '100000', 'quantity': 150, 'description': 'Exclusive networking dinner'},
            ]
        },
        # Cultural Arts Festival
        {
            'event': events[4],
            'tickets': [
                {'name': 'Festival Pass', 'price': '15000', 'quantity': 1500, 'description': 'Three-day festival access'},
                {'name': 'Family Package', 'price': '40000', 'quantity': 200, 'description': 'Admission for 2 adults + 2 children'},
            ]
        },
        # Mobile Dev Workshop
        {
            'event': events[5],
            'tickets': [
                {'name': 'Workshop Seat', 'price': '50000', 'quantity': 40, 'description': 'Full day workshop with materials'},
            ]
        }
    ]
    
    for event_tickets in ticket_types_data:
        event = event_tickets['event']
        for ticket_data in event_tickets['tickets']:
            ticket_type, created = TicketType.objects.get_or_create(
                event=event,
                name=ticket_data['name'],
                defaults={
                    'description': ticket_data['description'],
                    'price': Decimal(ticket_data['price']),
                    'currency': 'UGX',
                    'quantity': ticket_data['quantity'],
                    'ticket_type': 'general',
                    'sale_starts': timezone.now(),
                    'sale_ends': ticket_data.get('sale_ends', event.start_date - timedelta(hours=1)),
                    'is_active': True
                }
            )
            print(f"Created ticket type: {ticket_type.name} for {event.title}")
    
    print("\n✅ Sample data created successfully!")
    print(f"Created {len(organizers)} organizers")
    print(f"Created {len(users_data)} regular users")
    print(f"Created {len(categories)} categories")
    print(f"Created {len(venues)} venues")
    print(f"Created {len(events)} events")
    print(f"Created {len(tags)} tags")
    print("\nLogin credentials:")
    print("Admin: admin@eventflow.ug / admin123")
    print("Organizers: [organizer_email] / organizer123")
    print("Users: [user_email] / user123")

if __name__ == '__main__':
    create_sample_data()