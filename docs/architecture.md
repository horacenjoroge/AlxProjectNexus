# Architecture Documentation

## Overview

Provote is built using Django 5.0 with a microservices-ready architecture using Docker containers.

## System Architecture

```
┌─────────────┐
│   Nginx     │ (Reverse Proxy)
└──────┬──────┘
       │
┌──────▼──────┐
│   Django    │ (Gunicorn)
│   (Web)     │
└──────┬──────┘
       │
   ┌───┴───┬──────────┬──────────┐
   │       │          │          │
┌──▼──┐ ┌──▼──┐  ┌───▼───┐  ┌───▼────┐
│PostgreSQL│ │Redis│  │Celery│  │Celery │
│          │ │     │  │Worker│  │ Beat  │
└──────────┘ └─────┘  └──────┘  └───────┘
```

## Components

### Django Application
- **Framework**: Django 5.0.1
- **API**: Django REST Framework
- **WSGI Server**: Gunicorn (production)
- **ASGI**: Django ASGI (for future WebSocket support)

### Database
- **Primary DB**: PostgreSQL 15
- **Cache**: Redis 7
- **ORM**: Django ORM

### Background Tasks
- **Broker**: Redis
- **Worker**: Celery
- **Scheduler**: Celery Beat

### Web Server
- **Reverse Proxy**: Nginx
- **Static Files**: WhiteNoise (production) or Nginx
- **Media Files**: Nginx

## Application Structure

### Apps

1. **polls**: Poll management
   - Models: Poll, Choice
   - Views: PollViewSet
   - Serializers: PollSerializer, ChoiceSerializer

2. **votes**: Voting functionality
   - Models: Vote
   - Services: create_vote (with idempotency)
   - Views: VoteViewSet

3. **users**: User management
   - Models: UserProfile
   - Views: UserViewSet

4. **analytics**: Analytics and reporting
   - Models: PollAnalytics
   - Views: PollAnalyticsViewSet

### Core Utilities

- **middleware**: Rate limiting, audit logging
- **exceptions**: Custom voting exceptions
- **utils**: Idempotency, helpers

## Data Flow

### Vote Creation Flow

1. Client sends POST request with poll_id, choice_id, and optional idempotency_key
2. Rate limit middleware checks request rate
3. Audit log middleware logs the request
4. Vote service checks idempotency
5. Vote service validates poll and choice
6. Vote service creates vote in database
7. Response returned to client

## Security

- Rate limiting per IP
- CSRF protection
- SQL injection protection (Django ORM)
- XSS protection (Django templates)
- Secure headers (production)

## Scalability

- Horizontal scaling: Multiple Gunicorn workers
- Database connection pooling
- Redis caching
- Celery for async tasks
- Nginx load balancing (can be extended)

