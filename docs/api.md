# API Documentation

## Base URL

- Development: `http://localhost:8000/api/v1/`
- Production: `https://api.provote.com/api/v1/`

## Authentication

Currently using Django session authentication. Future: JWT tokens.

## Endpoints

### Polls

#### List Polls
```
GET /api/v1/polls/
```

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Poll Title",
      "description": "Poll description",
      "created_by": "username",
      "created_at": "2024-01-01T00:00:00Z",
      "is_open": true,
      "choices": [...]
    }
  ]
}
```

#### Create Poll
```
POST /api/v1/polls/
```

**Request Body:**
```json
{
  "title": "New Poll",
  "description": "Poll description",
  "starts_at": "2024-01-01T00:00:00Z",
  "ends_at": "2024-01-31T23:59:59Z",
  "is_active": true
}
```

#### Get Poll Details
```
GET /api/v1/polls/{id}/
```

#### Get Poll Results
```
GET /api/v1/polls/{id}/results/
```

**Response:**
```json
{
  "poll_id": 1,
  "poll_title": "Poll Title",
  "results": [
    {
      "choice_id": 1,
      "choice_text": "Choice 1",
      "votes": 10
    }
  ]
}
```

### Votes

#### List Votes
```
GET /api/v1/votes/
```

Returns votes for the authenticated user.

#### Create Vote
```
POST /api/v1/votes/create_vote/
```

**Request Body:**
```json
{
  "poll_id": 1,
  "choice_id": 1,
  "idempotency_key": "optional-key"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user": "username",
  "choice": "Choice 1",
  "poll": "Poll Title",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- `404`: Poll not found
- `400`: Invalid vote or poll closed
- `409`: Duplicate vote

### Users

#### List Users
```
GET /api/v1/users/
```

#### Get User Details
```
GET /api/v1/users/{id}/
```

### Analytics

#### List Analytics
```
GET /api/v1/analytics/
```

#### Get Poll Analytics
```
GET /api/v1/analytics/{id}/
```

## Idempotency

Vote creation supports idempotency keys. If you send the same request twice with the same idempotency key, the second request will return the same result without creating a duplicate vote.

## Rate Limiting

- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Per IP: 100 requests/minute (middleware)

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message"
}
```

Status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `409`: Conflict (duplicate)
- `429`: Too Many Requests
- `500`: Server Error

