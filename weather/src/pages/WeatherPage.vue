// WeatherPage.vue
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const searchQuery = ref('')
const currentLocation = ref('Unical, Rende, Calabria, Italy')
const currentTime = ref('')
const loading = ref(false)
const error = ref('')
const selectedDevice = ref(null)
const map = ref(null)
const markers = ref({})

// Weather data
const weatherData = ref({
  temperature: '—',
  feelsLike: '—',
  condition: 'Clear',
  description: 'Current weather conditions',
  airQuality: '—',
  wind: { speed: '—', direction: '—' },
  humidity: '—',
  visibility: '—',
  pressure: '—',
  dewPoint: '—',
  icon: '☀️',
  light: '—',
  noise: '—'
})

// Dynamic nearby locations from API
const nearbyLocations = ref([])

// Available measurements

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
let timer = null

// Update current time
function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit',
    hour12: true 
  })
}

// Reverse geocode to get location name from coordinates
async function getLocationName(latitude, longitude) {
  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`,
      {
        headers: {
          'User-Agent': 'WeatherApp/1.0'
        }
      }
    )
    
    if (!response.ok) throw new Error('Geocoding failed')
    
    const data = await response.json()
    const address = data.address || {}
    
    const locationParts = []
    
    if (address.road || address.street) {
      locationParts.push(address.road || address.street)
    } else if (address.suburb || address.neighbourhood) {
      locationParts.push(address.suburb || address.neighbourhood)
    }
    
    if (address.city || address.town || address.village) {
      locationParts.push(address.city || address.town || address.village)
    } else if (address.municipality) {
      locationParts.push(address.municipality)
    }
    
    if (address.state || address.province) {
      locationParts.push(address.state || address.province)
    }
    
    if (locationParts.length > 0) {
      return locationParts.join(', ')
    }
    
    if (data.display_name) {
      const parts = data.display_name.split(',').slice(0, 3)
      return parts.join(',')
    }
    
    return `Location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`
    
  } catch (error) {
    console.error('Reverse geocoding error:', error)
    return `Location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`
  }
}

// Initialize map
function initMap() {
  map.value = L.map('map-container').setView([39.358, 16.223], 13)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map.value)
}

// Add markers to map for all devices
function updateMapMarkers() {
  Object.values(markers.value).forEach(marker => {
    map.value.removeLayer(marker)
  })
  markers.value = {}
  
  nearbyLocations.value.forEach(device => {
    if (device.latitude && device.longitude) {
      const icon = L.divIcon({
        className: 'custom-marker',
        html: `
          <div style="
            background: ${selectedDevice.value?.device_id === device.device_id ? '#0d6efd' : '#dc3545'};
            color: white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            font-family: 'Times New Roman', serif;
          ">
            ${device.device_id}
          </div>
        `,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
      })
      
      const marker = L.marker([device.latitude, device.longitude], { icon })
        .addTo(map.value)
        .bindPopup(`
          <div style="font-family: 'Times New Roman', serif;">
            <strong>${device.locationName || device.name}</strong><br>
            <small>Device ID: ${device.device_id}</small><br>
            Temperature: ${device.temp}°F (${device.tempC}°C)<br>
            Humidity: ${device.humidity}%<br>
            Noise: ${device.noise} dB<br>
            Light: ${device.light}<br>
            <br>
            <small>📍 ${device.latitude.toFixed(4)}, ${device.longitude.toFixed(4)}</small>
          </div>
        `)
      
      marker.on('click', () => {
        selectDevice(device)
      })
      
      markers.value[device.device_id] = marker
    }
  })
  
  if (nearbyLocations.value.length > 0) {
    const bounds = L.latLngBounds(
      nearbyLocations.value.map(d => [d.latitude, d.longitude])
    )
    map.value.fitBounds(bounds, { padding: [50, 50] })
  }
}

// Fetch all devices and their latest weather
async function fetchDevices() {
  try {
    const devicePromises = availableMeasurements.map(async (device) => {
      try {
        const res = await fetch(
          `${API_BASE}/api/weather/forecast/?minutes=60&measurement=${device.measurement}`
        )
        if (!res.ok) return null
        
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) {
          const latest = data[data.length - 1]
          
          // Get location name from coordinates
          const locationName = await getLocationName(latest.latitude, latest.longitude)
          
          return {
            device_id: latest.device_id,
            measurement: device.measurement,
            name: `Robustel Device ${latest.device_id}`,
            locationName: locationName,
            temp: Math.round(latest.temperature * 9/5 + 32),
            tempC: latest.temperature,
            humidity: latest.humidity,
            pressure: latest.pressure,
            latitude: latest.latitude,
            longitude: latest.longitude,
            light: latest.light,
            noise: latest.noise,
            lastUpdate: latest.time
          }
        }
        return null
      } catch (e) {
        console.error(`Weather fetch error for ${device.measurement}:`, e)
        return null
      }
    })
    
    const results = await Promise.all(devicePromises)
    nearbyLocations.value = results.filter(device => device !== null)
    
    if (map.value) {
      updateMapMarkers()
    }
  } catch (e) {
    console.error('Device fetch error:', e)
  }
}

// Fetch weather data from API for main display
async function fetchWeatherData(measurement = 'Sensor_S6000U_data2') {
  try {
    loading.value = true
    error.value = ''
    
    const res = await fetch(
      `${API_BASE}/api/weather/forecast/?minutes=60&measurement=${measurement}`
    )
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
    const data = await res.json()

    if (Array.isArray(data) && data.length > 0) {
      const latest = data[data.length - 1]
      
      const tempF = Math.round(latest.temperature * 9/5 + 32)
      weatherData.value.temperature = tempF
      weatherData.value.humidity = latest.humidity
      weatherData.value.pressure = (latest.pressure / 1000).toFixed(2)
      weatherData.value.light = latest.light
      weatherData.value.noise = latest.noise
      weatherData.value.feelsLike = tempF - 2
      
      if (tempF > 80) {
        weatherData.value.condition = 'Hot'
        weatherData.value.icon = '☀️'
      } else if (tempF > 65) {
        weatherData.value.condition = 'Warm'
        weatherData.value.icon = '🌤️'
      } else if (tempF > 50) {
        weatherData.value.condition = 'Mild'
        weatherData.value.icon = '⛅'
      } else {
        weatherData.value.condition = 'Cool'
        weatherData.value.icon = '🌥️'
      }
      
      if (latest.noise < 40) {
        weatherData.value.airQuality = 45
      } else if (latest.noise < 60) {
        weatherData.value.airQuality = 75
      } else {
        weatherData.value.airQuality = 120
      }
      
      weatherData.value.description = `Temperature: ${latest.temperature}°C, Humidity: ${latest.humidity}%, Light: ${latest.light}, Noise: ${latest.noise}dB`
    }
  } catch (e) {
    error.value = String(e)
    console.error('Weather fetch error:', e)
  } finally {
    loading.value = false
  }
}

// Search location
function searchLocation() {
  if (searchQuery.value.trim()) {
    currentLocation.value = searchQuery.value.trim()
    searchQuery.value = ''
    fetchWeatherData()
  }
}

// Handle device selection and zoom to location
function selectDevice(device) {
  selectedDevice.value = device
  currentLocation.value = `${device.locationName} (${device.latitude.toFixed(4)}, ${device.longitude.toFixed(4)})`
  fetchWeatherData(device.measurement)
  
  if (map.value) {
    map.value.setView([device.latitude, device.longitude], 16, {
      animate: true,
      duration: 1
    })
    
    updateMapMarkers()
    
    if (markers.value[device.device_id]) {
      markers.value[device.device_id].openPopup()
    }
  }
  
  console.log(`Selected Device: ${device.device_id}`)
  console.log(`Location: ${device.locationName}`)
  console.log(`Coordinates: ${device.latitude}, ${device.longitude}`)
}

// Zoom controls
function zoomIn() {
  if (map.value) map.value.zoomIn()
}

function zoomOut() {
  if (map.value) map.value.zoomOut()
}

function resetView() {
  if (map.value && nearbyLocations.value.length > 0) {
    const bounds = L.latLngBounds(
      nearbyLocations.value.map(d => [d.latitude, d.longitude])
    )
    map.value.fitBounds(bounds, { padding: [50, 50] })
    selectedDevice.value = null
    currentLocation.value = 'Unical, Rende, Calabria, Italy'
    updateMapMarkers()
  }
}

function getAirQualityLevel(value) {
  if (value === '—') return { text: 'Unknown', color: 'secondary' }
  if (value <= 50) return { text: 'Good', color: 'success' }
  if (value <= 100) return { text: 'Moderate', color: 'warning' }
  if (value <= 150) return { text: 'Unhealthy', color: 'danger' }
  return { text: 'Very Unhealthy', color: 'danger' }
}

const airQualityInfo = computed(() => getAirQualityLevel(weatherData.value.airQuality))

onMounted(() => {
  updateTime()
  initMap()
  fetchDevices()
  fetchWeatherData()
  timer = setInterval(() => {
    updateTime()
    fetchDevices()
    if (selectedDevice.value) {
      fetchWeatherData(selectedDevice.value.measurement)
    } else {
      fetchWeatherData()
    }
  }, 300000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (map.value) map.value.remove()
})
</script>

<template>
  <div class="min-vh-100" style="background: linear-gradient(to bottom, #f5e6d3 0%, #e8d5c4 100%); font-family: 'Times New Roman', serif;">
    <!-- Header -->
    <div class="bg-white border-bottom shadow-sm">
      <div class="container-fluid">
        <div class="row align-items-center py-2">
          <div class="col-md-5">
            <div class="input-group">
              <input 
                v-model="searchQuery"
                @keyup.enter="searchLocation"
                type="text" 
                placeholder="Search for location"
                class="form-control"
                style="font-family: 'Times New Roman', serif;"
              />
              <button @click="searchLocation" class="btn btn-outline-secondary">
                <i class="bi bi-search"></i>
              </button>
            </div>
          </div>
          
          <div class="col-md-5">
            <span class="text-muted" style="font-family: 'Times New Roman', serif;">{{ currentLocation }} {{ weatherData.icon }} {{ weatherData.temperature }}°</span>
          </div>
          
          <div class="col-md-2 text-end">
            <button class="btn btn-link text-secondary">
              <i class="bi bi-three-dots-vertical fs-5"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Location Header -->
    <div class="container-fluid py-3">
      <div class="d-flex justify-content-between align-items-center">
        <h2 class="h4 mb-0" style="font-family: 'Times New Roman', serif;">
          {{ currentLocation }}
          <i class="bi bi-chevron-down"></i>
        </h2>
        <button class="btn btn-light rounded-circle" style="width: 40px; height: 40px;">
          <i class="bi bi-geo-alt-fill"></i>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="container-fluid">
      <div class="row g-3">
        <!-- Left Column - Weather Details -->
        <div class="col-lg-6">
          <div class="card shadow-sm">
            <div class="card-body">
              <!-- Header -->
              <div class="d-flex justify-content-between align-items-start mb-4">
                <div>
                  <h5 class="card-title mb-1" style="font-family: 'Times New Roman', serif;">Current weather</h5>
                  <small class="text-muted" style="font-family: 'Times New Roman', serif;">{{ currentTime }}</small>
                </div>
                <a href="#" class="text-decoration-none" style="font-family: 'Times New Roman', serif;">
                  <i class="bi bi-chat-dots me-1"></i>
                  <small>Seeing different weather?</small>
                </a>
              </div>

              <!-- Main Temperature Display -->
              <div class="d-flex align-items-center mb-3">
                <span class="display-1 me-3">{{ weatherData.icon }}</span>
                <div class="d-flex align-items-baseline">
                  <span class="display-1 fw-light" style="font-family: 'Times New Roman', serif;">{{ weatherData.temperature }}°F</span>
                  <div class="ms-3">
                    <p class="h5 mb-1" style="font-family: 'Times New Roman', serif;">{{ weatherData.condition }}</p>
                    <p class="text-muted mb-0" style="font-family: 'Times New Roman', serif;">Feels like {{ weatherData.feelsLike }}°</p>
                  </div>
                </div>
              </div>

              <p class="mb-4" style="font-family: 'Times New Roman', serif;">{{ weatherData.description }}</p>

              <!-- Weather Details Grid -->
              <div class="border-top pt-3">
                <div class="row g-3">
                  <div class="col-md-4 col-sm-6">
                    <div class="d-flex flex-column">
                      <small class="text-muted mb-1" style="font-family: 'Times New Roman', serif;">
                        Air quality <i class="bi bi-info-circle"></i>
                      </small>
                      <div class="d-flex align-items-center">
                        <span :class="`badge bg-${airQualityInfo.color} rounded-circle me-2`" style="width: 12px; height: 12px;"></span>
                        <strong style="font-family: 'Times New Roman', serif;">{{ weatherData.airQuality }} - {{ airQualityInfo.text }}</strong>
                      </div>
                    </div>
                  </div>

                  <div class="col-md-4 col-sm-6">
                    <div class="d-flex flex-column">
                      <small class="text-muted mb-1" style="font-family: 'Times New Roman', serif;">
                        Light Level <i class="bi bi-info-circle"></i>
                      </small>
                      <strong style="font-family: 'Times New Roman', serif;">{{ weatherData.light }}</strong>
                    </div>
                  </div>

                  <div class="col-md-4 col-sm-6">
                    <div class="d-flex flex-column">
                      <small class="text-muted mb-1" style="font-family: 'Times New Roman', serif;">
                        Humidity <i class="bi bi-info-circle"></i>
                      </small>
                      <strong style="font-family: 'Times New Roman', serif;">{{ weatherData.humidity }}%</strong>
                    </div>
                  </div>

                  <div class="col-md-4 col-sm-6">
                    <div class="d-flex flex-column">
                      <small class="text-muted mb-1" style="font-family: 'Times New Roman', serif;">
                        Noise Level <i class="bi bi-info-circle"></i>
                      </small>
                      <strong style="font-family: 'Times New Roman', serif;">{{ weatherData.noise }} dB</strong>
                    </div>
                  </div>

                  <div class="col-md-4 col-sm-6">
                    <div class="d-flex flex-column">
                      <small class="text-muted mb-1" style="font-family: 'Times New Roman', serif;">
                        Pressure <i class="bi bi-info-circle"></i>
                      </small>
                      <strong style="font-family: 'Times New Roman', serif;">{{ weatherData.pressure }} kPa</strong>
                    </div>
                  </div>

                  <div class="col-md-4 col-sm-6">
                    <div class="d-flex flex-column">
                      <small class="text-muted mb-1" style="font-family: 'Times New Roman', serif;">
                        Device <i class="bi bi-info-circle"></i>
                      </small>
                      <strong style="font-family: 'Times New Roman', serif;">{{ selectedDevice?.device_id || '—' }}</strong>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Loading Spinner -->
              <div v-if="loading" class="text-center mt-3">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                  <span class="visually-hidden">Loading...</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column - Map -->
        <div class="col-lg-6">
          <!-- Map Controls -->
          <div class="card shadow-sm mb-3">
            <div class="card-body p-2">
              <div class="btn-group w-100" role="group">
                <button type="button" class="btn btn-warning" style="font-family: 'Times New Roman', serif;">
                  <i class="bi bi-thermometer-half"></i> Temp
                </button>
                <button type="button" class="btn btn-outline-secondary" style="font-family: 'Times New Roman', serif;">
                  <i class="bi bi-droplet-fill"></i> Humid
                </button>
                <button type="button" class="btn btn-outline-secondary" style="font-family: 'Times New Roman', serif;">
                  <i class="bi bi-soundwave"></i> Noise
                </button>
              </div>
            </div>
          </div>

          <!-- Device List Card -->
          <div class="card shadow-sm mb-3">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
              <span style="font-family: 'Times New Roman', serif;"><strong>Devices</strong></span>
              <button @click="resetView" class="btn btn-sm btn-light" style="font-family: 'Times New Roman', serif;">
                <i class="bi bi-arrows-fullscreen"></i> Reset
              </button>
            </div>
            <div class="card-body p-2" style="max-height: 200px; overflow-y: auto;">
              <div 
                v-for="loc in nearbyLocations" 
                :key="loc.device_id"
                class="card shadow-sm mb-2 hover-card"
                :class="{ 'border-primary border-2 bg-light': selectedDevice?.device_id === loc.device_id }"
                style="cursor: pointer; transition: all 0.2s;"
                @click="selectDevice(loc)"
              >
                <div class="card-body p-2">
                  <div class="d-flex align-items-start">
                    <span class="fs-5 me-2">{{ weatherData.icon }}</span>
                    <div class="flex-grow-1">
                      <small class="d-block fw-bold" style="font-family: 'Times New Roman', serif;">{{ loc.locationName }}</small>
                      <small class="text-primary fw-semibold" style="font-family: 'Times New Roman', serif;">{{ loc.temp }}°F</small>
                      <small class="d-block text-muted" style="font-size: 0.65rem; font-family: 'Times New Roman', serif;">
                        📍 {{ loc.latitude?.toFixed(4) }}, {{ loc.longitude?.toFixed(4) }}
                      </small>
                      <small class="d-block text-muted" style="font-size: 0.65rem; font-family: 'Times New Roman', serif;">
                        💧 {{ loc.humidity }}% | 🔊 {{ loc.noise }}dB | ID: {{ loc.device_id }}
                      </small>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- No devices message -->
              <div v-if="nearbyLocations.length === 0" class="text-center text-muted p-3">
                <small style="font-family: 'Times New Roman', serif;">Loading devices...</small>
              </div>
            </div>
          </div>

          <!-- Map Container -->
          <div class="card shadow-sm overflow-hidden">
            <div class="position-relative">
              <div id="map-container" style="height: 400px; width: 100%;"></div>
              
              <!-- Zoom Controls Overlay -->
              <div class="position-absolute top-0 end-0 m-2" style="z-index: 1000;">
                <div class="btn-group-vertical shadow-sm">
                  <button @click="zoomIn" class="btn btn-light btn-sm" title="Zoom In">
                    <i class="bi bi-plus-lg"></i>
                  </button>
                  <button @click="zoomOut" class="btn btn-light btn-sm" title="Zoom Out">
                    <i class="bi bi-dash-lg"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- Map Footer -->
            <div class="bg-dark text-white p-3 d-flex justify-content-between align-items-center">
              <small style="font-family: 'Times New Roman', serif;">
                {{ selectedDevice 
                  ? `📍 ${selectedDevice.locationName}` 
                  : 'Select a device to view location' 
                }}
              </small>
              <button @click="resetView" class="btn btn-link btn-sm text-info text-decoration-none" style="font-family: 'Times New Roman', serif;">
                Reset
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Toast -->
    <div v-if="error" class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
      <div class="toast show" role="alert">
        <div class="toast-header bg-danger text-white">
          <i class="bi bi-exclamation-triangle me-2"></i>
          <strong class="me-auto" style="font-family: 'Times New Roman', serif;">Error</strong>
          <button type="button" class="btn-close btn-close-white" @click="error = ''" aria-label="Close"></button>
        </div>
        <div class="toast-body" style="font-family: 'Times New Roman', serif;">
          {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hover-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
}

:deep(.leaflet-popup-content) {
  font-family: 'Times New Roman', serif !important;
}

:deep(.leaflet-popup-content-wrapper) {
  font-family: 'Times New Roman', serif !important;
}

:deep(.custom-marker) {
  background: transparent !important;
  border: none !important;
}
</style>