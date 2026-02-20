# Quick Start Guide - API Authentication

## 🚀 Fast Setup (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy the `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` and update these values:
```env
FASTAPI_USERNAME=admin
FASTAPI_PASSWORD=admin123
SECRET_KEY=your-super-secret-key-change-in-production
```

### Step 3: Start the API
```bash
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 🔐 Authentication Methods

### Method 1: FastAPI Credentials (Easiest for Testing)

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/fastapi \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_role": "admin",
  "source": "fastapi"
}
```

**Use Token:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -X GET http://localhost:8000/api/weather/current \
  -H "Authorization: Bearer $TOKEN"
```

---

### Method 2: Firebase Authentication

**Prerequisites:**
- User account registered in Firebase database
- Email and password set

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login/firebase \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"userpassword"}'
```

**Use Token:**
```bash
TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -X GET http://localhost:8000/api/weather/current \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 Test Authentication

### Using Swagger UI (Browser)
1. Open: http://localhost:8000
2. Click on `/api/auth/login/fastapi`
3. Click "Try it out"
4. Enter: `{"username":"admin","password":"admin123"}`
5. Click "Execute"
6. Copy the `access_token`
7. Click "Authorize" at the top right
8. Paste: `Bearer <your_token>`
9. Now you can test other endpoints!

### Using Python
```bash
python test_authentication.py
```

### Using Node.js/JavaScript
```javascript
// Login
const response = await fetch('http://localhost:8000/api/auth/login/fastapi', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'admin', password: 'admin123'})
});

const {access_token} = await response.json();

// Use token
const data = await fetch('http://localhost:8000/api/weather/current', {
  headers: {'Authorization': `Bearer ${access_token}`}
});

console.log(await data.json());
```

---

## 📝 Example: Complete Python Script

```python
import requests

# 1. Login
response = requests.post(
    'http://localhost:8000/api/auth/login/fastapi',
    json={'username': 'admin', 'password': 'admin123'}
)
token = response.json()['access_token']
print(f"✓ Logged in with token: {token[:50]}...")

# 2. Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
result = requests.get(
    'http://localhost:8000/api/weather/current',
    headers=headers
)
print(f"✓ Response: {result.json()}")
```

---

## 🔧 API Endpoints

### Authentication Endpoints
```
POST /api/auth/login/fastapi        - Login with username/password
POST /api/auth/login/firebase       - Login with email/password
POST /api/auth/login                - Legacy Firebase login
```

### Protected Endpoints (Require Bearer Token)
```
GET  /api/weather/current           - Get current weather
POST /api/rag/chat                  - Chat with RAG assistant
GET  /health                        - Health check
```

---

## 🆘 Troubleshooting

### Error: "Cannot connect to API"
- Check API is running: `http://localhost:8000/health`
- Start with: `uvicorn app.main:app --reload`

### Error: "Invalid username or password"
- Check `.env` file has correct credentials
- Default: username=`admin`, password=`admin123`

### Error: "Invalid or expired token"
- Token has expired (default: 24 hours)
- Get a new token by logging in again
- For Firebase: token is managed by Firebase

### Error: "CORS error"
- Check ALLOWED_ORIGINS in `.env`
- Should include your frontend URL

---

## 📚 More Documentation

For detailed information, see:
- `API_AUTHENTICATION_GUIDE.md` - Complete authentication guide
- `.env.example` - All configuration options
- `test_authentication.py` - Full featured test suite

---

## 🔐 Security Reminders

✅ **DO:**
- Change `SECRET_KEY` to a random string in production
- Use HTTPS in production
- Store credentials in environment variables
- Set short token expiration times

❌ **DON'T:**
- Hardcode credentials in code
- Use default passwords in production
- Share your SECRET_KEY
- Send tokens over HTTP

---

## 🆘 Getting Help

1. Check the logs: Look for error messages in terminal
2. Test endpoints: Use `test_authentication.py`
3. Check configuration: Verify `.env` file is correct
4. Review docs: See `API_AUTHENTICATION_GUIDE.md`

---

**Ready to start? Run this:**
```bash
# Terminal 1: Start API
uvicorn app.main:app --reload

# Terminal 2: Run tests
python test_authentication.py
```

For detailed examples and usage, see `API_AUTHENTICATION_GUIDE.md` 📖
