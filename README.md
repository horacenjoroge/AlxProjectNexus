# Provote 🗳️

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0.1-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)

A professional Django-based voting platform with idempotent voting operations, real-time analytics, and comprehensive testing.

## 🚀 Features

- **Multi-environment Settings**: Separate configurations for development, production, and testing
- **Docker Support**: Full Docker Compose setup with PostgreSQL, Redis, Celery, and Nginx
- **Idempotent Voting**: Prevents duplicate votes with idempotency keys
- **RESTful API**: Django REST Framework with comprehensive endpoints
- **Real-time Analytics**: Poll analytics and vote tracking
- **Code Quality**: Pre-commit hooks with Black, Flake8, and isort
- **Comprehensive Testing**: Unit and integration tests with pytest

## 📋 Requirements

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/provote.git
cd provote
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Build and run with Docker

```bash
cd docker
docker-compose up --build
```

### 4. Run migrations

```bash
docker-compose exec web python manage.py migrate
```

### 5. Create a superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

## 🏗️ Project Structure

```
provote/
├── backend/                 # Django project
│   ├── apps/               # Django applications
│   │   ├── polls/          # Poll management
│   │   ├── votes/          # Voting functionality
│   │   ├── users/          # User management
│   │   └── analytics/      # Analytics and reporting
│   ├── config/             # Django configuration
│   │   └── settings/       # Environment-specific settings
│   ├── core/               # Core utilities
│   │   ├── middleware/     # Custom middleware
│   │   ├── exceptions/     # Custom exceptions
│   │   └── utils/          # Utility functions
│   └── tests/              # Integration tests
├── docker/                 # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── requirements/           # Python dependencies
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── docs/                   # Documentation
```

## 🧪 Testing

### Run all tests

```bash
docker-compose exec web pytest
```

### Run specific test categories

```bash
# Unit tests only
docker-compose exec web pytest -m unit

# Integration tests only
docker-compose exec web pytest -m integration

# With coverage
docker-compose exec web pytest --cov=backend --cov-report=html
```

### Test database connection

```bash
docker-compose exec web pytest backend/tests/test_integration.py::TestDatabaseConnection -v
```

### Test Redis connection

```bash
docker-compose exec web pytest backend/tests/test_integration.py::TestRedisConnection -v
```

## 🔧 Development

### Set up pre-commit hooks

```bash
pre-commit install
```

### Code formatting

```bash
# Format code with Black
black backend/

# Sort imports with isort
isort backend/

# Check code style with Flake8
flake8 backend/
```

### Run development server

```bash
docker-compose up
# Or locally:
cd backend
python manage.py runserver
```

## 📚 API Documentation

### Polls

- `GET /api/v1/polls/` - List all polls
- `POST /api/v1/polls/` - Create a new poll
- `GET /api/v1/polls/{id}/` - Get poll details
- `GET /api/v1/polls/{id}/results/` - Get poll results

### Votes

- `GET /api/v1/votes/` - List user's votes
- `POST /api/v1/votes/create_vote/` - Create a vote (idempotent)

### Users

- `GET /api/v1/users/` - List users
- `GET /api/v1/users/{id}/` - Get user details

### Analytics

- `GET /api/v1/analytics/` - List poll analytics
- `GET /api/v1/analytics/{id}/` - Get analytics for a poll

## 🐳 Docker Services

- **web**: Django application (Gunicorn)
- **db**: PostgreSQL database
- **redis**: Redis cache and message broker
- **celery**: Celery worker for background tasks
- **celery-beat**: Celery beat scheduler
- **nginx**: Reverse proxy and static file server

## 🔐 Environment Variables

See `.env.example` for all available environment variables. Key variables:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Database credentials
- `REDIS_HOST`, `REDIS_PORT`: Redis configuration
- `CELERY_BROKER_URL`: Celery broker URL

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

Made with ❤️ using Django

