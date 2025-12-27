<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AppShell from '../components/layout/AppShell.vue'
import SensorPanel from '../components/sensors/SensorPanel.vue'

const tabs = [
  { key: 'sources', label: 'SOURCES' },
  { key: 'buckets', label: 'BUCKETS' },
  { key: 'telegraph', label: 'TELEGRAPH' },
  { key: 'api', label: 'API TOKENS' },
]
const activeTab = ref('buckets')

const temperature = ref('—')
const humidity = ref('—')
const pressure = ref('—')
const deviceId = ref('—')
const observedAt = ref('No data')
const error = ref('')
const loading = ref(false)

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
let timer = null

async function loadLatest() {
  try {
    error.value = ''
    loading.value = true

    const res = await fetch(`${API_BASE}/api/weather/forecast/?minutes=60`)
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
    const data = await res.json()

    if (!Array.isArray(data) || data.length === 0) {
      temperature.value = '—'
      humidity.value = '—'
      pressure.value = '—'
      deviceId.value = '—'
      observedAt.value = 'No data'
      return
    }

    const last = data[data.length - 1]
    temperature.value = last.temperature ?? '—'
    humidity.value = last.humidity ?? '—'
    pressure.value = last.pressure ?? '—'
    deviceId.value = last.device_id ?? '—'
    observedAt.value = last.time ? new Date(last.time).toLocaleString() : '—'
  } catch (e) {
    error.value = String(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLatest()
  timer = setInterval(loadLatest, 15_000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function formatValue(v, unit) {
  if (v === '—' || v === null || v === undefined) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return `${n.toFixed(1)} ${unit}`
}
</script>

<template>
  <AppShell
    :breadcrumbs="['Università della Calabria', 'TELECOMMUNICATION ENGINEERING: SMART SENSING, COMPUTING AND NETWORKING', 'IOT-Smart Park Project']"
    title="Load Weather Data and Monitor Dashboard"
    
    v-model="activeTab"
  >
    <template #toolbar>
      <div class="d-flex flex-wrap gap-3 align-items-center">
        <div class="input-group" style="max-width: 520px;">
          <span class="input-group-text bg-black bg-opacity-25 border-secondary text-secondary">⌕</span>
          <input class="form-control bg-black bg-opacity-25 border-secondary text-white"
                 placeholder="Search based on device_ID..." />
        </div>

        <div class="d-flex gap-2 flex-shrink-0">
          <button class="btn btn-outline-secondary fw-bold" @click="emit('search')"> Search</button>
        </div>
      </div>
    </template>

    <SensorPanel
      title="Weather_data"
      :temperature="temperature"
      :humidity="humidity"
      :pressure="pressure"
      :device-id="deviceId"
      :observed-at="observedAt"
      :loading="loading"
      :error="error"
      :format-value="formatValue"
      @refresh="loadLatest"
    />
  </AppShell>
</template>