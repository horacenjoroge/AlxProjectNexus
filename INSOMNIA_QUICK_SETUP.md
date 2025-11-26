# Insomnia Quick Setup Guide

## Step 1: Create Environment Variables

1. In Insomnia, click **Environments** (top left)
2. Create a new environment called "Provote Local"
3. Add these variables:
   ```
   base_url = http://localhost:8001
   csrftoken = (leave empty - will be set automatically)
   sessionid = (leave empty - will be set automatically)
   ```

## Step 2: Create Requests (Fast Method)

### Request 1: Get CSRF Token (Pre-request)
- **Name:** `Get CSRF Token`
- **Method:** `GET`
- **URL:** `{{ base_url }}/admin/login/`
- **Purpose:** Gets CSRF token for login

**Test Script (to save CSRF token):**
```javascript
const cookies = insomnia.response.headers.find(h => h.name === 'Set-Cookie');
if (cookies) {
    const csrfMatch = cookies.value.match(/csrftoken=([^;]+)/);
    if (csrfMatch) {
        insomnia.environment.set('csrftoken', csrfMatch[1]);
    }
}
```

### Request 2: Login
- **Name:** `Login`
- **Method:** `POST`
- **URL:** `{{ base_url }}/admin/login/`
- **Body Type:** `Form URL Encoded`
- **Body:**
  ```
  username = provote_admin
  password = AProvote@14
  csrfmiddlewaretoken = {{ csrftoken }}
  ```
- **Headers:**
  ```
  Cookie: csrftoken={{ csrftoken }}
  Referer: {{ base_url }}/admin/login/
  ```

**Test Script (to save session):**
```javascript
if (insomnia.response.status === 302 || insomnia.response.status === 200) {
    const cookies = insomnia.response.headers.find(h => h.name === 'Set-Cookie');
    if (cookies) {
        const sessionMatch = cookies.value.match(/sessionid=([^;]+)/);
        if (sessionMatch) {
            insomnia.environment.set('sessionid', sessionMatch[1]);
        }
    }
}
```

### Request 3: List Polls
- **Name:** `List Polls`
- **Method:** `GET`
- **URL:** `{{ base_url }}/api/v1/polls/`
- **Headers:**
  ```
  Cookie: sessionid={{ sessionid }}; csrftoken={{ csrftoken }}
  X-CSRFToken: {{ csrftoken }}
  ```

### Request 4: Create Poll
- **Name:** `Create Poll`
- **Method:** `POST`
- **URL:** `{{ base_url }}/api/v1/polls/`
- **Headers:**
  ```
  Content-Type: application/json
  Cookie: sessionid={{ sessionid }}; csrftoken={{ csrftoken }}
  X-CSRFToken: {{ csrftoken }}
  ```
- **Body (JSON):**
  ```json
  {
    "title": "Test Poll",
    "description": "This is a test poll",
    "options": [
      {"text": "Option 1", "order": 0},
      {"text": "Option 2", "order": 1}
    ],
    "is_active": true,
    "is_draft": false
  }
  ```

**Test Script (to save poll_id):**
```javascript
if (insomnia.response.status === 201) {
    const data = JSON.parse(insomnia.response.body);
    if (data.id) {
        insomnia.environment.set('poll_id', data.id);
    }
}
```

### Request 5: Get Poll Details
- **Name:** `Get Poll Details`
- **Method:** `GET`
- **URL:** `{{ base_url }}/api/v1/polls/{{ poll_id }}/`
- **Headers:**
  ```
  Cookie: sessionid={{ sessionid }}; csrftoken={{ csrftoken }}
  X-CSRFToken: {{ csrftoken }}
  ```

### Request 6: Cast Vote
- **Name:** `Cast Vote`
- **Method:** `POST`
- **URL:** `{{ base_url }}/api/v1/votes/cast/`
- **Headers:**
  ```
  Content-Type: application/json
  Cookie: sessionid={{ sessionid }}; csrftoken={{ csrftoken }}
  X-CSRFToken: {{ csrftoken }}
  ```
- **Body (JSON):**
  ```json
  {
    "poll_id": {{ poll_id }},
    "choice_id": 1,
    "idempotency_key": "test-key-{{ $timestamp }}"
  }
  ```

### Request 7: List Votes
- **Name:** `List My Votes`
- **Method:** `GET`
- **URL:** `{{ base_url }}/api/v1/votes/my-votes/`
- **Headers:**
  ```
  Cookie: sessionid={{ sessionid }}; csrftoken={{ csrftoken }}
  X-CSRFToken: {{ csrftoken }}
  ```

### Request 8: Get User Details
- **Name:** `Get User Details`
- **Method:** `GET`
- **URL:** `{{ base_url }}/api/v1/users/1/`
- **Headers:**
  ```
  Cookie: sessionid={{ sessionid }}; csrftoken={{ csrftoken }}
  X-CSRFToken: {{ csrftoken }}
  ```

## Quick Copy-Paste Method

1. **Create a new Request Collection** in Insomnia
2. **Right-click the collection** → **Duplicate** to quickly create multiple requests
3. **For each request:**
   - Change the name
   - Update method/URL
   - Update headers/body
   - Copy-paste the test scripts

## Tips for Speed

1. **Use Request Templates:** Create one request, then duplicate it
2. **Use Environment Variables:** All URLs use `{{ base_url }}`
3. **Chain Requests:** Use test scripts to automatically save tokens/IDs
4. **Group by Feature:** Create folders (Polls, Votes, Users, etc.)

## Testing Flow

1. Run "Get CSRF Token" → saves csrftoken
2. Run "Login" → saves sessionid
3. Run "Create Poll" → saves poll_id
4. Run "Get Poll Details" → verify poll created
5. Run "Cast Vote" → vote on the poll
6. Run "List My Votes" → see your votes

