# Development Guide

## Getting Started

### Local Development Setup

1. **Clone and Install**

   ```bash
   git clone https://github.com/yourusername/provote.git
   cd provote
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements/development.txt
   ```

2. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with local settings
   ```

3. **Set up Database**

   ```bash
   # Using Docker for database and Redis
   cd docker
   docker-compose up -d db redis

   # Or use local PostgreSQL and Redis
   ```

4. **Run Migrations**

   ```bash
   cd backend
   python manage.py migrate
   ```

5. **Create Superuser**

   ```bash
   python manage.py createsuperuser
   ```

6. **Run Development Server**

   ```bash
   python manage.py runserver
   ```

## Code Style

### Black

Format code with Black:
```bash
black backend/
```

### isort

Sort imports:
```bash
isort backend/
```

### Flake8

Check code style:
```bash
flake8 backend/
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

## Testing

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest backend/tests/test_integration.py

# With coverage
pytest --cov=backend --cov-report=html

# Specific markers
pytest -m unit
pytest -m integration
```

### Test Database Connection

```bash
pytest backend/tests/test_integration.py::TestDatabaseConnection -v
```

### Test Redis Connection

```bash
pytest backend/tests/test_integration.py::TestRedisConnection -v
```

## Project Structure

### Adding a New App

1. Create app:
   ```bash
   python manage.py startapp myapp apps/myapp
   ```

2. Add to `INSTALLED_APPS` in `config/settings/base.py`

3. Create URL configuration

4. Add tests

### Adding a New Model

1. Create model in `models.py`
2. Create migration: `python manage.py makemigrations`
3. Apply migration: `python manage.py migrate`
4. Register in admin
5. Create serializer
6. Create view/viewset
7. Add URL route
8. Write tests

## Debugging

### Django Debug Toolbar

Enabled in development. Access at `/admin/` or any page.

### IPython

Use IPython shell:
```bash
python manage.py shell
```

### Logging

Logs are configured in `config/settings/base.py`. Adjust levels in development/production settings.

## Common Tasks

### Create Migration

```bash
python manage.py makemigrations
```

### Apply Migrations

```bash
python manage.py migrate
```

### Create Superuser

```bash
python manage.py createsuperuser
```

### Collect Static Files

```bash
python manage.py collectstatic
```

### Run Celery Worker

```bash
celery -A config worker --loglevel=info
```

### Run Celery Beat

```bash
celery -A config beat --loglevel=info
```

## Git Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run tests: `pytest`
4. Format code: `black . && isort .`
5. Commit: `git commit -m "Add feature"`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

## Troubleshooting

### Database Connection Issues

- Check `.env` file has correct database credentials
- Ensure PostgreSQL is running
- Check database exists

### Redis Connection Issues

- Ensure Redis is running
- Check `REDIS_HOST` and `REDIS_PORT` in `.env`

### Import Errors

- Ensure virtual environment is activated
- Check `PYTHONPATH` includes `backend/`
- Verify all dependencies installed

### Migration Issues

- Check for conflicting migrations
- Use `python manage.py showmigrations` to see status
- Reset if needed (development only): `python manage.py migrate --fake-initial`

