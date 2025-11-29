# Provote API - Quick Start Guide

## 🌐 Your API is Live!

**Base URL:** `https://reasonable-bravery-production.up.railway.app`

## 📚 Interactive Documentation (Easiest Way)

1. **Swagger UI** (Recommended): https://reasonable-bravery-production.up.railway.app/api/docs/
   - Interactive API explorer
   - Test endpoints directly in the browser
   - See request/response examples

2. **ReDoc**: https://reasonable-bravery-production.up.railway.app/api/redoc/
   - Alternative documentation format
   - Clean, readable interface

## 🔑 Step 1: Get an Authentication Token

To use the API, you need a Bearer token. Here's how to get one:

### Option A: Using cURL

```bash
curl -X POST https://reasonable-bravery-production.up.railway.app/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "token": "abc123xyz...",
  "user_id": 1,
  "username": "your_username"
}
```

### Option B: Using the Interactive Docs

1. Go to https://reasonable-bravery-production.up.railway.app/api/docs/
2. Find the **`POST /api/v1/auth/token/`** endpoint
3. Click "Try it out"
4. Enter your username and password
5. Click "Execute"
6. Copy the token from the response

## 🚀 Step 2: Make API Calls

### Example: Create a Poll

```bash
curl -X POST https://reasonable-bravery-production.up.railway.app/api/v1/polls/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "question": "What is your favorite programming language?",
    "description": "Let us know your preference",
    "choices": [
      {"text": "Python"},
      {"text": "JavaScript"},
      {"text": "Java"},
      {"text": "Go"}
    ],
    "is_public": true,
    "allow_multiple_choices": false
  }'
```

### Example: Get All Polls

```bash
curl -X GET https://reasonable-bravery-production.up.railway.app/api/v1/polls/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Example: Vote on a Poll

```bash
curl -X POST https://reasonable-bravery-production.up.railway.app/api/v1/votes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "poll": 1,
    "choices": [1],
    "idempotency_key": "unique-key-12345"
  }'
```

## 📋 Available Endpoints

From the API root (`/api/v1/`), you can access:

- **Polls**: `/api/v1/polls/` - Create, read, update polls
- **Votes**: `/api/v1/votes/` - Cast votes on polls
- **Users**: `/api/v1/users/` - User management
- **Analytics**: `/api/v1/analytics/` - Poll analytics
- **Notifications**: `/api/v1/notifications/` - User notifications
- **Categories**: `/api/v1/categories/` - Poll categories
- **Tags**: `/api/v1/tags/` - Poll tags

## 🛠️ Using with API Clients

### Postman
1. Import the OpenAPI schema from: https://reasonable-bravery-production.up.railway.app/api/schema/?format=json
2. Set up environment variable `base_url` = `https://reasonable-bravery-production.up.railway.app`
3. Get token and set as Bearer token in Authorization tab

### Insomnia
1. Import the OpenAPI schema from: https://reasonable-bravery-production.up.railway.app/api/schema/?format=json
2. Set up environment variable `base_url` = `https://reasonable-bravery-production.up.railway.app`
3. Get token and set as Bearer token in Auth tab

### Python (requests library)

```python
import requests

BASE_URL = "https://reasonable-bravery-production.up.railway.app"
TOKEN = "your_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get all polls
response = requests.get(f"{BASE_URL}/api/v1/polls/", headers=headers)
polls = response.json()
print(polls)
```

### JavaScript (fetch API)

```javascript
const BASE_URL = "https://reasonable-bravery-production.up.railway.app";
const TOKEN = "your_token_here";

const headers = {
  "Authorization": `Bearer ${TOKEN}`,
  "Content-Type": "application/json"
};

// Get all polls
fetch(`${BASE_URL}/api/v1/polls/`, { headers })
  .then(response => response.json())
  .then(data => console.log(data));
```

## 🔍 Testing the API

### Quick Health Check

```bash
curl https://reasonable-bravery-production.up.railway.app/health/
```

**Expected Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "cache": "healthy"
  },
  "version": "1.0.0"
}
```

## 📖 Full Documentation

For complete API documentation, visit:
- **Swagger UI**: https://reasonable-bravery-production.up.railway.app/api/docs/
- **ReDoc**: https://reasonable-bravery-production.up.railway.app/api/redoc/
- **OpenAPI Schema**: https://reasonable-bravery-production.up.railway.app/api/schema/

## 🎯 Next Steps

1. **Explore the API**: Visit `/api/docs/` to see all available endpoints
2. **Get a Token**: Use `/api/v1/auth/token/` to authenticate
3. **Create a Poll**: Use `/api/v1/polls/` to create your first poll
4. **Cast Votes**: Use `/api/v1/votes/` to vote on polls
5. **View Analytics**: Use `/api/v1/analytics/` to see poll statistics

---

**Note**: Replace `YOUR_TOKEN_HERE` with the actual token you receive from the authentication endpoint.

