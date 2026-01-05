// RagChatbot.vue - RAG-based Chatbot Component
<script setup>
import { ref, computed, nextTick } from 'vue'

const isOpen = ref(false)
const isMinimized = ref(false)
const isMaximized = ref(false)
const messages = ref([])
const userInput = ref('')
const loading = ref(false)
const deviceContext = ref([])

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// Fetch device data for RAG context
async function fetchDeviceContext() {
  try {
    const res = await fetch(`${API_BASE}/api/weather/forecast/?minutes=1440`) // Last 24 hours
    if (!res.ok) throw new Error('Failed to fetch device data')
    const data = await res.json()
    deviceContext.value = data
    return data
  } catch (e) {
    console.error('Error fetching device context:', e)
    deviceContext.value = []
    return []
  }
}

// Build context from database for RAG
function buildContext() {
  if (deviceContext.value.length === 0) {
    return "No device data available in the database."
  }
  
  // Group by device and get latest readings
  const deviceMap = new Map()
  deviceContext.value.forEach(reading => {
    const deviceId = reading.device_id || 'unknown'
    if (!deviceMap.has(deviceId) || new Date(reading.time) > new Date(deviceMap.get(deviceId).time)) {
      deviceMap.set(deviceId, reading)
    }
  })
  
  let context = "Available IoT Weather Devices and Current Readings:\n\n"
  deviceMap.forEach((reading, deviceId) => {
    context += `Device ID: ${deviceId}\n`
    context += `- Temperature: ${reading.temperature}°C\n`
    context += `- Humidity: ${reading.humidity}%\n`
    context += `- Pressure: ${reading.pressure} hPa\n`
    context += `- Last Updated: ${new Date(reading.time).toLocaleString()}\n\n`
  })
  
  return context
}

// Send message to RAG LLM API
async function sendMessage() {
  if (!userInput.value.trim()) return
  
  const userMessage = userInput.value.trim()
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date().toLocaleTimeString()
  })
  
  userInput.value = ''
  loading.value = true
  
  try {
    // Fetch latest device data
    await fetchDeviceContext()
    
    // Build context from database
    const context = buildContext()
    
    // Create RAG prompt
    const ragPrompt = `You are an IoT weather monitoring assistant. You have access to the following device data from the database:

${context}

IMPORTANT INSTRUCTIONS:
- Only answer questions using the data provided above from the database.
- If the user asks about information not present in the database, respond with: "I don't have any information about that in the current database."
- Be concise and specific when referencing device IDs and their readings.
- Format temperature in Celsius, humidity as percentage, and pressure in hPa.
- Do not make up or assume any data that is not explicitly provided above.

User Question: ${userMessage}

Answer based only on the database information provided above:`

    // Call your RAG LLM API endpoint
    const response = await fetch(`${API_BASE}/api/rag/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: ragPrompt,
        context: context,
        user_query: userMessage
      })
    })
    
    if (!response.ok) {
      throw new Error('RAG API request failed')
    }
    
    const data = await response.json()
    const botResponse = data.response || data.answer || "I don't have any information about that in the current database."
    
    messages.value.push({
      role: 'assistant',
      content: botResponse,
      timestamp: new Date().toLocaleTimeString()
    })
    
  } catch (error) {
    console.error('Error calling RAG API:', error)
    messages.value.push({
      role: 'assistant',
      content: "I don't have any information about that in the current database.",
      timestamp: new Date().toLocaleTimeString()
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  const chatContainer = document.getElementById('chat-messages')
  if (chatContainer) {
    chatContainer.scrollTop = chatContainer.scrollHeight
  }
}

function toggleChat() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    isMinimized.value = false
    fetchDeviceContext()
    if (messages.value.length === 0) {
      messages.value.push({
        role: 'assistant',
        content: 'Hello! I\'m your IoT Weather Assistant. I can answer questions about the devices and weather data in our database. What would you like to know?',
        timestamp: new Date().toLocaleTimeString()
      })
    }
    nextTick(() => scrollToBottom())
  }
}

function minimizeChat() {
  isMinimized.value = !isMinimized.value
  if (isMinimized.value) {
    isMaximized.value = false
  }
}

function maximizeChat() {
  isMaximized.value = !isMaximized.value
  isMinimized.value = false
}

function closeChat() {
  isOpen.value = false
  isMinimized.value = false
  isMaximized.value = false
}

function clearChat() {
  messages.value = []
  messages.value.push({
    role: 'assistant',
    content: 'Chat cleared. How can I help you with device data?',
    timestamp: new Date().toLocaleTimeString()
  })
}

const chatContainerClass = computed(() => {
  if (isMaximized.value) return 'chat-maximized'
  if (isMinimized.value) return 'chat-minimized'
  return 'chat-normal'
})
</script>

<template>
  <div>
    <!-- Floating Action Button -->
  <button 
    v-if="!isOpen"
    class="chat-fab btn btn-primary rounded-circle shadow-lg"
    @click="toggleChat"
    title="Open RAG Chatbot"
  >
    <i class="bi bi-chat-dots-fill fs-4"></i>
  </button>

  <!-- Chat Window -->
  <div
    v-if="isOpen"
    :class="['chat-container', chatContainerClass, 'shadow-lg']"
  >
    <!-- Chat Header -->
    <div class="chat-header bg-primary text-white d-flex align-items-center justify-content-between p-3">
      <div class="d-flex align-items-center">
        <i class="bi bi-robot fs-4 me-2"></i>
        <div>
          <h6 class="mb-0">IoT Weather Assistant</h6>
          <small class="opacity-75">RAG-powered chatbot</small>
        </div>
      </div>
      <div class="d-flex gap-2">
        <button 
          class="btn btn-sm btn-outline-light border-0"
          @click="minimizeChat"
          title="Minimize"
        >
          <i class="bi bi-dash-lg"></i>
        </button>
        <button 
          class="btn btn-sm btn-outline-light border-0"
          @click="maximizeChat"
          title="Maximize/Restore"
        >
          <i :class="isMaximized ? 'bi bi-fullscreen-exit' : 'bi bi-fullscreen'"></i>
        </button>
        <button 
          class="btn btn-sm btn-outline-light border-0"
          @click="closeChat"
          title="Close"
        >
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    </div>

    <!-- Chat Body -->
    <div v-if="!isMinimized" class="chat-body">
      <!-- Messages Area -->
      <div id="chat-messages" class="chat-messages p-3">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="['message-bubble', message.role === 'user' ? 'user-message' : 'assistant-message']"
        >
          <div class="message-content">
            <div class="message-text">{{ message.content }}</div>
            <small class="message-time">{{ message.timestamp }}</small>
          </div>
        </div>
        
        <!-- Loading Indicator -->
        <div v-if="loading" class="message-bubble assistant-message">
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="chat-input border-top p-3">
        <div class="d-flex gap-2 mb-2">
          <button 
            class="btn btn-sm btn-outline-secondary"
            @click="clearChat"
            title="Clear chat"
          >
            <i class="bi bi-trash"></i> Clear
          </button>
          <button 
            class="btn btn-sm btn-outline-primary"
            @click="fetchDeviceContext"
            title="Refresh device data"
          >
            <i class="bi bi-arrow-clockwise"></i> Refresh Data
          </button>
          <small class="text-muted ms-auto align-self-center">
            {{ deviceContext.length }} readings loaded
          </small>
        </div>
        <div class="input-group">
          <input 
            v-model="userInput"
            @keyup.enter="sendMessage"
            type="text"
            class="form-control"
            placeholder="Ask about devices, temperature, humidity..."
            :disabled="loading"
          />
          <button 
            class="btn btn-primary"
            @click="sendMessage"
            :disabled="loading || !userInput.trim()"
          >
            <i class="bi bi-send-fill"></i>
          </button>
        </div>
        <small class="text-muted d-block mt-2">
          <i class="bi bi-info-circle"></i> I only answer questions based on data in our database
        </small>
      </div>
    </div>

    <!-- Minimized Preview -->
    <div v-else class="chat-minimized-preview p-2 text-center bg-light" @click="minimizeChat">
      <small class="text-muted">{{ messages.length }} messages - Click to expand</small>
    </div>
  </div>
  </div>
</template>

<style scoped>
/* Floating Action Button */
.chat-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 64px;
  height: 64px;
  z-index: 1000;
  transition: transform 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-fab:hover {
  transform: scale(1.1);
}

/* Chat Container */
.chat-container {
  position: fixed;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  z-index: 1050;
  display: flex;
  flex-direction: column;
}

.chat-normal {
  bottom: 24px;
  right: 24px;
  width: 400px;
  height: 600px;
}

.chat-minimized {
  bottom: 24px;
  right: 24px;
  width: 300px;
  height: auto;
}

.chat-maximized {
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw !important;
  height: 100vh !important;
  border-radius: 0;
  margin: 0;
}

/* Chat Header */
.chat-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.chat-header .btn {
  padding: 0.25rem 0.5rem;
}

.chat-header .btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Chat Body */
.chat-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  background: #f8f9fa;
  min-height: 0;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Message Bubbles */
.message-bubble {
  margin-bottom: 16px;
  display: flex;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  justify-content: flex-end;
}

.assistant-message {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.user-message .message-content {
  background: #0d6efd;
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant-message .message-content {
  background: white;
  color: #212529;
  border-bottom-left-radius: 4px;
  border: 1px solid #e9ecef;
}

.message-text {
  margin-bottom: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.5;
}

.message-time {
  font-size: 0.7rem;
  opacity: 0.7;
  display: block;
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.assistant-message .message-time {
  color: #6c757d;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6c757d;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-8px);
  }
}

/* Chat Input */
.chat-input {
  background: white;
  flex-shrink: 0;
}

.chat-input .form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

/* Minimized Preview */
.chat-minimized-preview {
  cursor: pointer;
}

.chat-minimized-preview:hover {
  background: #e9ecef !important;
}

/* Responsive */
@media (max-width: 768px) {
  .chat-normal {
    width: calc(100vw - 48px);
    height: calc(100vh - 100px);
    bottom: 12px;
    right: 12px;
  }
  
  .chat-fab {
    width: 56px;
    height: 56px;
    bottom: 16px;
    right: 16px;
  }
  
  .message-content {
    max-width: 85%;
  }
}

@media (max-width: 480px) {
  .chat-normal {
    width: calc(100vw - 24px);
    height: calc(100vh - 80px);
    bottom: 8px;
    right: 8px;
  }
  
  .message-content {
    max-width: 90%;
  }
}
</style>