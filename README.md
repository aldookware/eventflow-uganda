# EventFlow - Event Booking Platform

A comprehensive event booking platform built for Uganda, featuring Django REST API, Next.js admin dashboard, and Flutter mobile app.

## 🚀 Features

- **Multi-role Authentication** (User/Organizer/Admin)
- **Event Management** with approval workflow
- **QR Code Tickets** and check-in system
- **Mobile Money Payments** (MTN MoMo, Airtel Money)
- **SMS OTP Verification** via local telecom providers
- **Real-time Notifications** and analytics
- **Location-based Event Discovery**

## 🏗️ Architecture

- **Backend**: Django REST Framework with PostgreSQL
- **Admin Dashboard**: Next.js with TypeScript & Tailwind CSS
- **Mobile App**: Flutter with Riverpod state management
- **Caching**: Redis for sessions and caching
- **Queue Processing**: Celery for background tasks

## 🛠️ Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Flutter 3.0+
- PostgreSQL 14+
- Redis 6+

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd ticket_rise

# Backend
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Admin Dashboard
cd ../admin
npm install
npm run dev

# Mobile App
cd ../mobile
flutter pub get
flutter run
```

### Docker Setup

```bash
docker-compose up -d
```

## 📱 Mobile App Features

- Event discovery and search
- Secure booking with Mobile Money
- QR ticket generation
- Real-time notifications
- Profile management

## 🖥️ Admin Dashboard

- Event approval workflow
- User and organizer management
- Analytics and reporting
- Payment tracking
- Content moderation

## 🌍 Uganda-Specific Features

- SMS OTP via MTN/Airtel networks
- Mobile Money integration
- UGX currency support
- East Africa Time (UTC+3)
- English/Luganda language support

## 🧪 Testing

```bash
# Backend tests
cd backend && python manage.py test

# Frontend tests  
cd admin && npm test

# Mobile tests
cd mobile && flutter test
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.