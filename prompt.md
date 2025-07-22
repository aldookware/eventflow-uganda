# GitHub Copilot Prompt (Django + Flutter Event Booking Platform)

You are helping me bootstrap a full‑stack **Event Booking Platform**.

## Goal

Generate an initial codebase with clean, modular architecture.

## Stack

* **Backend/Admin:** Django + Django REST Framework, PostgreSQL, Redis (cache + Celery), JWT auth (`simplejwt`), role-based permissions (Admin/User/Organizer), Django Admin customization.
* **Mobile:** **Flutter** (User + Organizer apps in one codebase with feature modules), state management (Riverpod), Dio REST client, secure storage for tokens, Stripe payments, Firebase Auth (for social + phone/OTP), Firebase Cloud Messaging for push, Google Maps.
* Docker Compose for local dev.

## Django Domain Apps

`users`, `profiles`, `events`, `tickets`, `bookings`, `payments`, `commissions`, `notifications`, `media`, `support`, `analytics`, `activitylog`.

## Key Models

User, OrganizerProfile, Event, Venue, VenueAmenity, SeatingPlan, TicketType, Booking, Payment, Refund, DiscountCode, AddOnService, CommissionRule, Invoice, Notification, SupportTicket, ActivityLog, Review, MediaAsset.

## Core Features

Auth & profiles, event lifecycle (draft→pending→approved/published, recurring), search/filter, booking & QR tickets, refunds, commissions/payouts, media moderation, analytics dashboards, notifications (push/email/SMS via Celery), support tickets, admin management.

**Additional Functionalities:**

* **Seating & Capacity:** Seating plans, seat counts per ticket tier.
* **Discounts & Offers:** Promo/discount codes applied at checkout.
* **Add‑Ons & Services:** Food, beverage, parking, etc., selectable during booking.
* **Extended Event Metadata:** Age limit, dress code, tags, amenities.
* **Ratings & Reviews:** Users rate/review events; feed into analytics.
* **Organizer Cancellation Penalties:** Automatic penalty handling in refund workflow.
* **Tax‑Compliant Invoices & Reports:** Generate downloadable invoices and financial reports.
* **User Activity Logs:** Track login/logout, event views, bookings.
* **Venue Management:** Amenities, photos, operating hours, capacity details.

## Flutter Screen Slices

### Shared Foundations

* **Bootstrap/Splash:** Initialize services, check auth token.
* **Onboarding / Auth Flow:**

  * Welcome / Intro Carousel
  * Login (email/password)
  * Register (email/phone)
  * Phone OTP Verification
  * Social Login Buttons (Google/Facebook)
  * Forgot Password / Reset
* **Main Shell:** BottomNav (Home, Search, Bookings, Favorites, Profile)
* **Common Widgets:** EventCard, TicketTierSelector, Loading/Empty states, Error dialogs.

### User App Screens

1. **Home Feed:** Recommended events, categories, banners.
2. **Search & Filter:** Keyword search, filters (category, date range, price range, radius), map toggle.
3. **Map View:** Google Map with event markers; tap → preview sheet.
4. **Event Detail:** Description, media carousel, ticket tiers, crowd level, favorites toggle, share, “Book Now.”
5. **Booking Flow:**

   * Select Tickets/Add‑ons
   * Attendee Details
   * Payment (Stripe) + Summary
   * Success Confirmation (QR code)
6. **My Bookings:**

   * Upcoming / Past tabs
   * Booking Detail (QR code, refund request button, status)
7. **QR Ticket Viewer:** Fullscreen QR with event info.
8. **Favorites:** Events & Artists list.
9. **Calendar View:** Booked events calendar.
10. **Media Upload:** Post crowd photo/video → pending moderation.
11. **Notifications Center:** List + detail.
12. **Support:** Create ticket, ticket thread view.
13. **Profile:** View/edit profile, interests, saved payment methods, logout.
14. **Settings:** Privacy, notification toggles, delete account.

### Organizer App Screens (role‑gated within same app)

1. **Organizer Dashboard:** KPIs (tickets sold, revenue, check‑ins).
2. **My Events List:** Draft/Pending/Published tabs.
3. **Create/Edit Event Wizard:**

   * Basic Info
   * Schedule & Recurrence
   * Venue & Map location
   * Ticket Tiers & Inventory
   * Media Upload
   * Visibility & Publish
4. **Event Detail (Organizer View):** Stats, edit, publish/unpublish, delete.
5. **Check‑In Scanner:** Camera QR scanner → mark attendance.
6. **Live Attendance:** List of checked‑in attendees, search.
7. **Sales & Analytics:** Charts (tickets over time, revenue by tier).
8. **Commission & Payouts:** Payout history, pending amounts.
9. **Media Moderation Queue:** Approve/Reject user uploads.
10. **Support Tickets (Organizer):** View/respond to tickets tied to their events.
11. **Organizer Profile / Verification:** Upload documents, status (approved/pending).

### Admin (optional mobile access)

Can rely on Django Admin initially.

## Non‑Functional

Validation, error handling, logging, rate limiting (DRF throttling), S3 file storage, environment configs, sample data seeding (management command), pytest tests, README.

## Instructions to Copilot

1. **Backend:** Generate Django project and apps; implement models, serializers, viewsets, routers, permissions; Celery tasks (notification sending, payout calculations, cancellation penalties); Stripe integration placeholders; invoice generation utilities; management command to seed sample data (including seating plans, discounts, add‑ons); unit test examples.
2. **Flutter:** Create modular folder structure (`lib/features/...`), Riverpod providers, routing (`go_router`), services (auth, events, bookings), JSON models, repository pattern, mock data fixtures, and scaffold all screens above with minimal UI & TODOs.
3. Add comments/TODOs for unimplemented logic.
4. Provide README summarizing setup, migrations, running backend & mobile.

**Produce the code now.**