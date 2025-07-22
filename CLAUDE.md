# TicketRise/EventFlow - Event Booking Platform

## Project Overview

Full-stack event booking platform with Django backend and Flutter mobile app. Brand name: **EventFlow** with tagline "Discover. Plan. Experience."

**Target Market**: Uganda - requires SMS OTP verification and local payment methods.

## Tech Stack

- **Backend**: Django + Django REST Framework, PostgreSQL, Redis, Celery, JWT auth
- **Admin UI**: Next.js (React) with TypeScript, Tailwind CSS
- **Mobile**: Flutter with Riverpod state management, Firebase auth, Stripe payments
- **Infrastructure**: Docker Compose for local development

## Project Structure

```text
/
├── backend/           # Django REST API
├── admin/            # Next.js admin dashboard
├── mobile/           # Flutter app
├── mobile-app-screens/ # UI mockups and designs
└── prompt.md         # Detailed project requirements
```

## Key Features

- Multi-role auth (User/Organizer/Admin)
- Event lifecycle management (draft→pending→published)
- QR code ticket system
- Stripe payment integration
- Location-based event discovery
- Seating plans and capacity management
- Commission and payout system
- Real-time notifications
- Media upload and moderation

## Uganda-Specific Requirements

- **SMS OTP Verification**: Integration with Uganda telecom providers (MTN, Airtel)
- **Payment Methods**: Mobile Money (MTN MoMo, Airtel Money), bank transfers
- **Currency**: Ugandan Shilling (UGX) support
- **Language**: English primary, potential Luganda support
- **Timezone**: East Africa Time (EAT, UTC+3)

## Django Apps

`users`, `profiles`, `events`, `tickets`, `bookings`, `payments`, `commissions`, `notifications`, `media`, `support`, `analytics`, `activitylog`

## Flutter Features

- Role-based UI (User/Organizer views)
- Event discovery with maps integration
- Booking flow with payment processing
- QR ticket generation and scanning
- Push notifications
- Profile management

## Development Commands

```bash
# Backend
cd backend
python manage.py runserver
python manage.py migrate
python manage.py collectstatic

# Admin Dashboard
cd admin
npm run dev
npm run build
npm run start

# Mobile App
cd mobile
flutter run
flutter test
flutter build apk

# Docker
docker-compose up -d
docker-compose logs -f
```

## Design System

- Primary color: Purple (#8B5CF6)
- Clean, modern UI with card-based layouts
- Bottom navigation pattern
- Material Design principles for Flutter

## API Structure

RESTful API with JWT authentication, role-based permissions, and comprehensive event management endpoints.

## Admin Dashboard Features

- Event management and approval workflow
- User and organizer management
- Analytics and reporting dashboards
- Payment and commission tracking
- Content moderation
- System configuration
