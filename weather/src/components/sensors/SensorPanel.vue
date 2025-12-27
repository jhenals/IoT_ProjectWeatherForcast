<script setup>
  import logo from '@/assets/Logo.svg'
defineProps({
  title: { type: String, default: 'Weather_data' },
  temperature: { type: [String, Number], default: '—' },
  humidity: { type: [String, Number], default: '—' },
  pressure: { type: [String, Number], default: '—' },
  deviceId: { type: String, default: '—' },
  observedAt: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  formatValue: { type: Function, required: true },
})

const emit = defineEmits(['refresh'])
</script>

<template>
  <div class="card bg-dark border" style="border-color: rgba(255,255,255,.10) !important;">
    <div class="card-body">
      <div class="d-flex justify-content-between align-items-start gap-3">
        <div class="flex-grow-1" style="min-width:0;">
          <div class="h2 fw-bold mb-1">{{ title }}</div>

          <div class="text-secondary small d-flex flex-wrap gap-2 align-items-center">
            <span class="h4 fw-bold mb-2 text-white">Device: {{ deviceId }}</span>
            <span class="text-white-50">•</span>
            <span class="h4 fw-bold mb-2 text-white">Observed: {{ observedAt }}</span>
          </div>

          <div class="mt-3 d-flex flex-wrap gap-2">
            <img :src="logo" alt="Logo" width="50" height="50"/>
            <span class=" text-bg-light p-2 fs-4">
              Temperature: {{ formatValue(temperature, '°C') }}
            </span>
            <span class=" text-bg-light text-dark p-2 fs-4">
              Humidity: {{ formatValue(humidity, '%') }}
            </span>
            <span class=" text-bg-light text-dark p-2 fs-4">
              Pressure: {{ formatValue(pressure, 'hPa') }}
            </span>
          </div>

          <div v-if="error" class="text-danger small mt-2">Error: {{ error }}</div>
        </div>

        <div class="d-flex gap-2 flex-shrink-0">
          <button class="btn btn-outline-primary fw-bold" @click="emit('refresh')"> Refresh</button>
        </div>
      </div>

      <div v-if="loading" class="d-flex align-items-center gap-2 mt-3 text-primary large">
        <div class="spinner-border spinner-border-sm" role="status"></div>
        <span>Loading…</span>
      </div>
    </div>
  </div>
</template>
