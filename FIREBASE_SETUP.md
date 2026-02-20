# Firebase Setup for IoT Weather Forecast API

This application now uses **Firebase Authentication** and **Firestore** (same database as the web-app) instead of SQLite.

## Setup Instructions

### 1. Get Firebase Service Account Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `smart-park-iot-d7743`
3. Go to **Project Settings** → **Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file securely

### 2. Set Environment Variables

Add these to your `.env` file:

```env
# Firebase Credentials (from downloaded JSON)
FIREBASE_PROJECT_ID=smart-park-iot-d7743
FIREBASE_PRIVATE_KEY_ID=<private_key_id>
FIREBASE_PRIVATE_KEY=<private_key>
FIREBASE_CLIENT_EMAIL=<client_email>
FIREBASE_CLIENT_ID=<client_id>
FIREBASE_CERT_URL=<cert_url>
```

**Important**: 
- The `FIREBASE_PRIVATE_KEY` must have `\n` characters replaced with actual newlines in the code (already handled in database.py)
- Keep these credentials secure; never commit them to version control

### 3. Alternative: Service Account Key File

Instead of environment variables, you can set:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 4. Verify Setup

Run a quick health check:
```bash
curl http://localhost:8000/
```

## API Endpoints

### Register New User
**POST** `/api/auth/register`

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Response:
```json
{
  "message": "User created successfully"
}
```

### Login
**POST** `/api/auth/login`

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Response:
```json
{
  "access_token": "firebase_id_token",
  "token_type": "bearer"
}
```

## Database Structure

Users are stored in Firestore at: `users/{uid}`

```
{
  "email": "user@example.com",
  "role": "visitor",  // or "admin"
  "created_at": "2026-02-20T12:00:00.000000",
  "uid": "firebase_user_id"
}
```

## Shared Database

This application now shares the same Firestore database as the web-app, so:
- Users registered in the web-app can log in here
- Users registered here can log in in the web-app
- All user data is synchronized across both applications

## Troubleshooting

### "Firebase initialization failed"
- Check that `FIREBASE_PRIVATE_KEY` is correctly formatted with newlines
- Verify all required environment variables are set

### "Email already registered"
- The email exists in Firebase Auth
- Try logging in instead of registering

### "Invalid email or password"
- Double-check credentials
- Ensure the user was successfully registered first
