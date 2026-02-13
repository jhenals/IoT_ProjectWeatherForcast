# 🌦️ IoT Weather Forecast - Park Administration System
<img width="1337" height="504" alt="image" src="https://github.com/user-attachments/assets/076df49d-3e28-40ac-bf36-88c5d23ed27f" />


This repository contains a full-stack solution for a specialized weather station system designed for Park Administrators. It features a **FastAPI** backend for processing IoT sensor data and a **Vue.js** frontend for real-time visualization.

## 🚀 Features

* **Real-time Dashboard:** Built with Vue.js for reactive data updates.
* **High Performance:** FastAPI backend for asynchronous data handling.
* **IoT Integration:** Designed to process sensor data from remote weather stations.
* **Park Management:** Tailored tools for administrators to monitor micro-climates.

---

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yonasyifter/IoT_ProjectWeatherForcast.git
cd IoT_ProjectWeatherForcast

```

### 2. Backend Setup (FastAPI)

It is recommended to use a virtual environment:

```bash
# Create and activate virtual environment
python -m venv venv
# On Windows: venv\Scripts\activate | On macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

### 3. Frontend Setup (Vue.js)

Ensure you have [Node.js and npm](https://nodejs.org/) installed.

```bash
# Navigate to the frontend directory (e.g., /frontend or /client)
cd weather

# Install dependencies
npm install

```

---

## 🏃 Running the Application

To run the full system, you will need to start both the backend and frontend servers.

### Start the Backend

From the root directory:

```bash
uvicorn main:app --reload

```

* **API Documentation:** Access [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/api)

### Start the Frontend

From the frontend directory:

```bash
npm run dev

```

* **Local Access:** Usually available at [http://localhost:5173](https://www.google.com/search?q=http://localhost:5173) (Vite) or [http://localhost:8080](https://www.google.com/search?q=http://localhost:8080).

---

## 📁 Project Structure

```text
├── app/                # FastAPI Application
│   ├── main.py
    ├── config.py
│   ├── influx.py
    ├── schemas.py       # Entry point
│   ├── requirements.txt    # Python dependencies
│   └── routes/                # weather.py
├── frontend/               # Vue.js Application
│   ├── src/
  │   ├── asset/
  │   ├── components/
  │   ├── pages/              # Components and Views
│   ├── package.json        # Node dependencies
│   └── public/             # Static assets
└── README.md

```

## 🤝 Contributing

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.


# Smart Park RAG Chat - Groq Integration

A voice-enabled AI assistant for Smart Park using **Groq** for ultra-fast inference and **Whisper** for speech transcription.

## ⚡ Why Groq?

- **Lightning-fast inference**: Up to 10x faster than traditional cloud APIs
- **Whisper-large-v3-turbo**: Best-in-class speech transcription
- **Llama 3.3 70B**: Powerful language understanding
- **Cost-effective**: Competitive pricing with excellent performance

## 🚀 Features

- 🎤 **Voice Input**: Hold-to-record with automatic transcription via Groq Whisper
- 💬 **Text Chat**: Type questions directly
- 🌡️ **Sensor Integration**: Real-time park weather data (temperature, humidity by zone)
- ⚡ **Ultra-Fast**: Powered by Groq's lightning-fast LPU inference
- 📱 **Mobile Friendly**: Responsive design with touch support

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+ (for Vue.js frontend)
- Groq API key (free tier available at https://console.groq.com/)

## 🔧 Backend Setup

### 1. Install Dependencies

```bash
pip install -r requirements_groq.txt
```

### 2. Get Your Groq API Key

1. Visit https://console.groq.com/keys
2. Sign up or log in
3. Create a new API key
4. Copy the key

### 3. Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Groq API key
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
```

### 4. Add Route to FastAPI

In your `main.py` or where you register routes:

```python
from fastapi import FastAPI
from routes.rag import router as rag_router  # Import the Groq RAG router

app = FastAPI()

# Register the RAG route
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])

# Your other routes...
```

### 5. Run the Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🎨 Frontend Setup (Vue.js)

### 1. Replace Component

Replace your existing RAG chat component with `RagChatGroq.vue`:

```bash
cp RagChatGroq.vue src/components/RagChatGroq.vue
```

### 2. Configure API Base URL

In your `.env` or `.env.local`:

```bash
VITE_API_BASE=http://localhost:8000
```

### 3. Use the Component

In your Vue app:

```vue
<template>
  <div id="app">
    <!-- Your other components -->
    <RagChatGroq />
  </div>
</template>

<script setup>
import RagChatGroq from './components/RagChatGroq.vue';
</script>
```

## 🎯 API Endpoint

### POST `/api/rag/chat`

**Request (multipart/form-data):**

```
- user_query: string (optional) - Text query from user
- audio_file: file (optional) - Audio recording (WAV, OGG, WebM, MP3, etc.)
- device_data: string (optional) - JSON array of sensor data
```

**Response (JSON):**

```json
{
  "transcript": "What's the weather like in Zone A?",
  "answer": "In Zone A (Main Entrance), the current temperature is 24°C with 60% humidity."
}
```

## 📊 Sensor Data Format

The `device_data` field should be a JSON string containing an array of sensor readings:

```json
[
  {
    "device_id": "Zone A - Main Entrance",
    "temperature": 24,
    "humidity": 60
  },
  {
    "device_id": "Zone B - Playground",
    "temperature": 23,
    "humidity": 65
  }
]
```

## 🎤 Audio Formats Supported

Groq Whisper supports the following audio formats:
- WAV (recommended)
- OGG
- WebM
- MP3
- FLAC
- M4A
- MP4
- MPEG
- MPGA

**Maximum file size**: 25MB

## 🔍 How It Works

### Voice Input Flow:

1. **User holds mic button** → MediaRecorder captures audio
2. **User releases** → Audio blob sent to backend
3. **Backend receives audio** → Saves temporarily
4. **Groq Whisper transcribes** → Returns text transcript
5. **Groq Llama processes** → Generates answer using sensor context
6. **Frontend displays** → Shows both transcript and answer

### Text Input Flow:

1. **User types question** → Frontend validates
2. **Sends to backend** → With sensor context
3. **Groq Llama processes** → Generates answer
4. **Frontend displays** → Shows answer

## 🛠️ Troubleshooting

### Issue: "Could not reach the server"
- **Solution**: Ensure backend is running on port 8000
- Check `VITE_API_BASE` environment variable
- Verify no CORS issues

### Issue: "Audio transcription failed"
- **Solution**: Check audio format is supported
- Ensure file size is under 25MB
- Verify `GROQ_API_KEY` is set correctly

### Issue: "Missing device_data"
- **Solution**: Backend now uses fallback data if sensor API fails
- Check `/api/weather/forecast/` endpoint is working
- View browser console for detailed logs

### Issue: Microphone not working
- **Solution**: Browser needs HTTPS or localhost
- Check browser permissions
- Try different audio format (WAV instead of WebM)

## 📈 Performance

- **Groq Whisper transcription**: ~1-2 seconds for 10-second audio
- **Groq Llama response**: ~0.5-1 second for typical queries
- **Total latency**: ~2-3 seconds end-to-end (voice → answer)

Compare to traditional APIs: 5-10+ seconds

## 💰 Pricing

Groq offers competitive pricing:
- **Free tier**: Great for development and testing
- **Pay-as-you-go**: Very cost-effective for production

Check latest pricing at: https://groq.com/pricing/

## 🔐 Security Best Practices

1. **Never commit** `.env` file to version control
2. **Use environment variables** for API keys
3. **Implement rate limiting** in production
4. **Validate user inputs** on backend
5. **Set appropriate CORS** policies

## 📚 Models Used

- **Speech-to-Text**: `whisper-large-v3-turbo`
  - Fast, accurate transcription
  - Supports 100+ languages
  
- **Chat**: `llama-3.3-70b-versatile`
  - Powerful language understanding
  - Fast inference on Groq LPUs
  - Alternative: `mixtral-8x7b-32768` for longer contexts

## 🚦 Rate Limits

Groq has generous rate limits. For the free tier:
- Check current limits at: https://console.groq.com/settings/limits

If you hit rate limits, consider:
- Implementing request queuing
- Adding user-side rate limiting
- Upgrading to paid tier

## 📞 Support

- **Groq Docs**: https://console.groq.com/docs
- **Groq Discord**: Join for community support
- **GitHub Issues**: Report bugs in your repository

## 🎉 Next Steps

1. ✅ Set up Groq API key
2. ✅ Test with audio and text
3. 🔄 Integrate with real sensor data
4. 🎨 Customize UI/UX
5. 🚀 Deploy to production

## 📝 License

[Your License Here]

---

**Built with ⚡ by Groq, 🎤 Whisper, and 🦙 Llama**
