<!-- ChartPage.vue - Enhanced Interactive Grafana-like Dashboard -->
<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

/* -----------------------
 * State
 * --------------------- */
const selectedDevice = ref('101')
const timeRange = ref('6h')
const bucketMinutes = ref(5)
const refreshSeconds = ref(30)
const selectedVisualization = ref('line')

const chartData = ref([])
const availableDevices = ref([])
const loading = ref(false)
const error = ref('')

const zoomLevel = ref(1)
const panX = ref(0)
const panY = ref(0)
const hoveredPoint = ref(null)
const selectedPoints = ref([])
const showStats = ref(true)
const showGrid = ref(true)

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

/* -----------------------
 * Chart constants
 * --------------------- */
const svgWidth = 800
const svgHeight = 350

const PADDING = { left: 50, right: 30, top: 20, bottom: 30 }
const innerWidth = svgWidth - PADDING.left - PADDING.right
const innerHeight = svgHeight - PADDING.top - PADDING.bottom

let timer = null

const visualizationTypes = [
  { id: 'line', label: 'Line Chart', icon: 'bi-graph-up', number: '1' },
  { id: 'area', label: 'Area Chart', icon: 'bi-graph-up', number: '2' },
  { id: 'bar', label: 'Bar Chart', icon: 'bi-bar-chart', number: '3' },
  { id: 'scatter', label: 'Scatter Plot', icon: 'bi-scatter', number: '4' },
  { id: 'pie', label: 'Pie Chart', icon: 'bi-pie-chart', number: '5' }
]

/* -----------------------
 * Helpers
 * --------------------- */
function toNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function minutesForRange(range) {
  const ranges = { '1h': 60, '6h': 360, '24h': 1440, '7d': 10080, '30d': 43200 }
  return ranges[range] || 360
}

function formatTs(ts) {
  try {
    return new Date(ts).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

function xForIndex(i, len) {
  if (len <= 1) return PADDING.left + innerWidth / 2
  return PADDING.left + (innerWidth * i) / (len - 1)
}

function yForValue(v, min, max) {
  if (v == null) return null
  const range = max - min || 1
  const t = (v - min) / range
  return PADDING.top + (1 - t) * innerHeight
}

function bucketize(rows) {
  const bm = bucketMinutes.value
  if (!bm || bm <= 0) return rows

  const bucketMs = bm * 60 * 1000
  const m = new Map()

  for (const r of rows) {
    const b = Math.floor(r.t / bucketMs) * bucketMs
    const cur = m.get(b) || { t: b, tempSum: 0, humSum: 0, presSum: 0, tempN: 0, humN: 0, presN: 0 }

    if (r.temperature != null) { cur.tempSum += r.temperature; cur.tempN++ }
    if (r.humidity != null) { cur.humSum += r.humidity; cur.humN++ }
    if (r.pressure != null) { cur.presSum += r.pressure; cur.presN++ }
    m.set(b, cur)
  }

  return [...m.values()].sort((a, b) => a.t - b.t).map(b => ({
    t: b.t,
    temperature: b.tempN ? b.tempSum / b.tempN : null,
    humidity: b.humN ? b.humSum / b.humN : null,
    pressure: b.presN ? b.presSum / b.presN : null
  }))
}

/* -----------------------
 * Fetch data
 * --------------------- */
async function loadChartData() {
  loading.value = true
  error.value = ''
  hoveredPoint.value = null
  selectedPoints.value = []
  resetView()

  try {
    const minutes = minutesForRange(timeRange.value)
    const url = new URL(`${API_BASE}/api/weather/forecast/`)
    url.searchParams.set('minutes', String(minutes))

    const res = await fetch(url.toString())
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
    const data = await res.json()

    if (!Array.isArray(data)) throw new Error('Unexpected API response')

    const uniqueDevices = [...new Set(data.map(d => String(d.device_id ?? 'unknown')))].sort()
    availableDevices.value = uniqueDevices

    const filtered = data.filter(d => String(d.device_id) === String(selectedDevice.value))
    
    const normalized = filtered
      .map(d => ({
        t: new Date(d.time).getTime(),
        temperature: toNum(d.temperature),
        humidity: toNum(d.humidity),
        pressure: toNum(d.pressure)
      }))
      .filter(d => Number.isFinite(d.t))
      .sort((a, b) => a.t - b.t)

    chartData.value = bucketize(normalized)
  } catch (e) {
    error.value = String(e?.message || e)
    chartData.value = []
    availableDevices.value = []
  } finally {
    loading.value = false
  }
}

/* -----------------------
 * Stats
 * --------------------- */
function avgOf(key) {
  const vals = chartData.value.map(d => d[key]).filter(v => v != null)
  if (!vals.length) return 0
  return vals.reduce((a, b) => a + b, 0) / vals.length
}

function minOf(key) {
  const vals = chartData.value.map(d => d[key]).filter(v => v != null)
  return vals.length ? Math.min(...vals) : 0
}

function maxOf(key) {
  const vals = chartData.value.map(d => d[key]).filter(v => v != null)
  return vals.length ? Math.max(...vals) : 0
}

const avgTemperature = computed(() => avgOf('temperature'))
const avgHumidity = computed(() => avgOf('humidity'))
const avgPressure = computed(() => avgOf('pressure'))

const minTemperature = computed(() => minOf('temperature'))
const maxTemperature = computed(() => maxOf('temperature'))
const minHumidity = computed(() => minOf('humidity'))
const maxHumidity = computed(() => maxOf('humidity'))
const minPressure = computed(() => minOf('pressure'))
const maxPressure = computed(() => maxOf('pressure'))

const selectedPointStats = computed(() => {
  if (selectedPoints.value.length === 0) return null
  const temps = selectedPoints.value.map(p => p.temp).filter(v => v != null)
  const hums = selectedPoints.value.map(p => p.hum).filter(v => v != null)
  const press = selectedPoints.value.map(p => p.pres).filter(v => v != null)
  
  return {
    tempAvg: temps.length ? (temps.reduce((a, b) => a + b) / temps.length).toFixed(2) : '—',
    humAvg: hums.length ? (hums.reduce((a, b) => a + b) / hums.length).toFixed(2) : '—',
    presAvg: press.length ? (press.reduce((a, b) => a + b) / press.length).toFixed(2) : '—',
    count: selectedPoints.value.length
  }
})

/* -----------------------
 * Series builders
 * --------------------- */
function buildSeries(key, minV, maxV) {
  const len = chartData.value.length
  const pts = []
  for (let i = 0; i < len; i++) {
    const row = chartData.value[i]
    const v = row?.[key] ?? null
    const x = xForIndex(i, len)
    const y = yForValue(v, minV, maxV)
    if (y != null) {
      pts.push({ x, y, v, t: row.t, i })
    }
  }
  return pts
}

const temperatureSeries = computed(() => buildSeries('temperature', minTemperature.value, maxTemperature.value))
const humiditySeries = computed(() => buildSeries('humidity', minHumidity.value, maxHumidity.value))
const pressureSeries = computed(() => buildSeries('pressure', minPressure.value, maxPressure.value))

function polylinePoints(series) {
  return series.map(p => `${p.x},${p.y}`).join(' ')
}

function areaPath(series) {
  if (!series.length) return ''
  const first = series[0]
  const last = series[series.length - 1]
  const topLine = series.map(p => `${p.x},${p.y}`).join(' ')
  const baseY = PADDING.top + innerHeight
  return `M ${first.x},${baseY} L ${topLine} L ${last.x},${baseY} Z`
}

const temperatureLinePoints = computed(() => polylinePoints(temperatureSeries.value))
const humidityLinePoints = computed(() => polylinePoints(humiditySeries.value))
const pressureLinePoints = computed(() => polylinePoints(pressureSeries.value))

const temperatureAreaPath = computed(() => areaPath(temperatureSeries.value))
const humidityAreaPath = computed(() => areaPath(humiditySeries.value))
const pressureAreaPath = computed(() => areaPath(pressureSeries.value))

/* -----------------------
 * Bar helpers
 * --------------------- */
function barRects(series, minV, maxV) {
  const len = chartData.value.length || 1
  const spacing = innerWidth / len
  const bw = Math.max(6, Math.min(22, spacing * 0.7))
  const baseY = PADDING.top + innerHeight
  const range = maxV - minV || 1

  return series.map(p => {
    const t = (p.v - minV) / range
    const h = Math.max(1, t * innerHeight)
    return { x: p.x - bw / 2, y: baseY - h, w: bw, h, v: p.v, t: p.t, i: p.i }
  })
}

const tempBars = computed(() => barRects(temperatureSeries.value, minTemperature.value, maxTemperature.value))
const humBars = computed(() => barRects(humiditySeries.value, minHumidity.value, maxHumidity.value))
const presBars = computed(() => barRects(pressureSeries.value, minPressure.value, maxPressure.value))

/* -----------------------
 * Pie segments
 * --------------------- */
const pieSegments = computed(() => {
  const temp = avgTemperature.value
  const hum = avgHumidity.value
  const pres = avgPressure.value / 100

  const total = temp + hum + pres
  if (!total) return []

  const data = [
    { label: 'Temperature', value: temp, color: '#ef4444' },
    { label: 'Humidity', value: hum, color: '#3b82f6' },
    { label: 'Pressure', value: pres, color: '#10b981' }
  ]

  const segments = []
  let startAngle = 0
  for (const item of data) {
    const pct = (item.value / total) * 100
    const angle = (pct / 100) * 360
    segments.push({
      ...item,
      percentage: pct.toFixed(1),
      startAngle,
      angle
    })
    startAngle += angle
  }
  return segments
})

function generatePiePath(startAngle, angle) {
  const radius = 80
  const centerX = 150
  const centerY = 120

  const startRad = ((startAngle - 90) * Math.PI) / 180
  const endRad = ((startAngle + angle - 90) * Math.PI) / 180

  const x1 = centerX + radius * Math.cos(startRad)
  const y1 = centerY + radius * Math.sin(startRad)

  const x2 = centerX + radius * Math.cos(endRad)
  const y2 = centerY + radius * Math.sin(endRad)

  const largeArc = angle > 180 ? 1 : 0

  return `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`
}

/* -----------------------
 * Point selection
 * --------------------- */
function togglePointSelection(type, i, temp, hum, pres, t) {
  const key = `${type}-${i}`
  const existing = selectedPoints.value.findIndex(p => p.key === key)
  
  if (existing >= 0) {
    selectedPoints.value.splice(existing, 1)
  } else {
    selectedPoints.value.push({ key, type, i, temp, hum, pres, t })
  }
}

function isPointSelected(type, i) {
  return selectedPoints.value.some(p => p.key === `${type}-${i}`)
}

function clearSelection() {
  selectedPoints.value = []
}

/* -----------------------
 * Zoom & Pan
 * --------------------- */
const isPanning = ref(false)
let panStart = null

const svgTransformStyle = computed(() => ({
  width: '100%',
  height: '100%',
  transform: `translate(${panX.value}px, ${panY.value}px) scale(${zoomLevel.value})`,
  transformOrigin: 'top left',
  transition: isPanning.value ? 'none' : 'transform 0.15s ease'
}))

function zoomIn() {
  zoomLevel.value = Math.min(zoomLevel.value + 0.2, 3)
}

function zoomOut() {
  zoomLevel.value = Math.max(zoomLevel.value - 0.2, 1)
}

function resetView() {
  zoomLevel.value = 1
  panX.value = 0
  panY.value = 0
}

function handleWheel(event) {
  event.preventDefault()
  if (event.deltaY < 0) zoomIn()
  else zoomOut()
}

function onPanMove(e) {
  if (!isPanning.value || !panStart) return
  panX.value = panStart.x + (e.clientX - panStart.startX)
  panY.value = panStart.y + (e.clientY - panStart.startY)
}

function endPan() {
  isPanning.value = false
  panStart = null
  window.removeEventListener('mousemove', onPanMove)
  window.removeEventListener('mouseup', endPan)
}

function startPan(e) {
  if (e.button !== 0) return
  isPanning.value = true
  panStart = {
    startX: e.clientX,
    startY: e.clientY,
    x: panX.value,
    y: panY.value
  }
  window.addEventListener('mousemove', onPanMove)
  window.addEventListener('mouseup', endPan)
}

/* -----------------------
 * Timer
 * --------------------- */
function stopTimer() {
  if (timer) clearInterval(timer)
  timer = null
}

function startTimer() {
  stopTimer()
  if (!refreshSeconds.value || refreshSeconds.value <= 0) return
  timer = setInterval(loadChartData, refreshSeconds.value * 1000)
}

watch(refreshSeconds, startTimer)
watch([selectedDevice, timeRange, bucketMinutes], () => loadChartData())

onMounted(() => {
  loadChartData()
  startTimer()
})

onBeforeUnmount(() => {
  stopTimer()
  endPan()
})
</script>

<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="header">
      <div class="header-top">
        <h1 class="header-title">
          <i class="bi bi-graph-up"></i>
          Sensor Analytics Dashboard
        </h1>
        <div class="live-badge" :class="{ updating: loading }">
          <span class="pulse"></span>
          {{ loading ? 'Updating...' : 'Live' }}
        </div>
      </div>
      <p class="header-subtitle">Real-time monitoring and visualization of IoT sensors</p>
    </div>

    <!-- Controls -->
    <div class="panel">
      <div class="controls-grid">
        <div>
          <label class="label"><i class="bi bi-hdd"></i> Device ID</label>
          <input v-model="selectedDevice" type="text" class="input" placeholder="Enter device ID (e.g., 101, 102)" />
          <div class="help">
            <strong>Available devices:</strong>
            {{ availableDevices.length ? availableDevices.join(', ') : (loading ? 'Loading…' : '—') }}
          </div>
        </div>

        <div>
          <label class="label"><i class="bi bi-calendar"></i> Time Range</label>
          <select v-model="timeRange" class="input">
            <option value="1h">Last 1 Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>

        <div>
          <label class="label"><i class="bi bi-clock"></i> Aggregation</label>
          <select v-model.number="bucketMinutes" class="input">
            <option :value="0">Raw Data</option>
            <option :value="1">1 Minute</option>
            <option :value="5">5 Minutes</option>
            <option :value="15">15 Minutes</option>
            <option :value="60">1 Hour</option>
          </select>
        </div>

        <div>
          <label class="label"><i class="bi bi-arrow-repeat"></i> Auto Refresh</label>
          <select v-model.number="refreshSeconds" class="input">
            <option :value="0">Off</option>
            <option :value="10">Every 10s</option>
            <option :value="30">Every 30s</option>
            <option :value="60">Every 60s</option>
          </select>
        </div>

        <div class="load-wrap">
          <button class="btn btn-primary" @click="loadChartData" :disabled="loading">
            <i :class="loading ? 'bi bi-hourglass-split' : 'bi bi-arrow-clockwise'"></i>
            {{ loading ? 'Loading…' : 'Load Data' }}
          </button>
        </div>
      </div>

      <div v-if="error" class="error">
        <i class="bi bi-exclamation-triangle"></i>
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- Tool Bar -->
    <div class="toolbar">
      <button class="tool-btn" :class="{ active: showStats }" @click="showStats = !showStats" title="Toggle stats cards">
        <i class="bi bi-speedometer2"></i> Stats
      </button>
      <button class="tool-btn" :class="{ active: showGrid }" @click="showGrid = !showGrid" title="Toggle grid">
        <i class="bi bi-grid-3x3"></i> Grid
      </button>
      <button class="tool-btn" @click="clearSelection" v-if="selectedPoints.length" title="Clear point selection">
        <i class="bi bi-x-circle"></i> Clear ({{ selectedPoints.length }})
      </button>
      <div style="flex: 1;"></div>
      <span class="toolbar-info">💡 Ctrl+Click points • Scroll to zoom • Drag to pan</span>
    </div>

    <!-- Stats Cards -->
    <div v-if="chartData.length && showStats" class="stats-grid">
      <div class="stat stat-temp">
        <div class="stat-label"><i class="bi bi-thermometer-half"></i> Temperature</div>
        <div class="stat-value">{{ avgTemperature.toFixed(1) }}°C</div>
        <div class="stat-sub">Min: {{ minTemperature.toFixed(1) }}°C · Max: {{ maxTemperature.toFixed(1) }}°C</div>
      </div>

      <div class="stat stat-hum">
        <div class="stat-label"><i class="bi bi-droplet-half"></i> Humidity</div>
        <div class="stat-value">{{ avgHumidity.toFixed(1) }}%</div>
        <div class="stat-sub">Min: {{ minHumidity.toFixed(1) }}% · Max: {{ maxHumidity.toFixed(1) }}%</div>
      </div>

      <div class="stat stat-pres">
        <div class="stat-label"><i class="bi bi-speedometer2"></i> Pressure</div>
        <div class="stat-value">{{ avgPressure.toFixed(1) /1000 }} kPa</div>
        <div class="stat-sub">Min: {{ minPressure.toFixed(1) }} · Max: {{ maxPressure.toFixed(1) }}</div>
      </div>

      <div class="stat stat-count">
        <div class="stat-label"><i class="bi bi-graph-up"></i> Data Points</div>
        <div class="stat-value">{{ chartData.length }}</div>
        <div class="stat-sub">Range: {{ timeRange }} · Bucket: {{ bucketMinutes ? `${bucketMinutes}m` : 'raw' }}</div>
      </div>

      <div v-if="selectedPointStats" class="stat stat-selected">
        <div class="stat-label"><i class="bi bi-hand-index-thumb"></i> Selected ({{ selectedPointStats.count }})</div>
        <div class="stat-row">
          <span class="stat-row-item">T: {{ selectedPointStats.tempAvg }}°C</span>
          <span class="stat-row-item">H: {{ selectedPointStats.humAvg }}%</span>
          <span class="stat-row-item">P: {{ selectedPointStats.presAvg /1000}} kPa</span>
        </div>
      </div>
    </div>

    <!-- Visualization selector -->
    <div class="panel viz-panel" v-if="chartData.length">
      <div class="viz-title">Visualization Type:</div>
      <button
        v-for="viz in visualizationTypes"
        :key="viz.id"
        class="viz-btn"
        :class="{ active: selectedVisualization === viz.id }"
        @click="selectedVisualization = viz.id"
      >
        <span class="viz-num">{{ viz.number }}</span>
        <i :class="`bi ${viz.icon}`"></i>
        {{ viz.label }}
      </button>
    </div>

    <!-- Pie Chart -->
    <div v-if="chartData.length && selectedVisualization === 'pie'" class="panel chart-panel">
      <h3 class="chart-title"><i class="bi bi-pie-chart"></i> Summary (Average Values)</h3>
      <div class="chart-wrap">
        <div class="pie-wrap">
          <svg viewBox="0 0 300 240" class="pie-svg">
            <circle cx="150" cy="120" r="80" fill="none" stroke="#2d3748" stroke-width="1" style="opacity: 0.35" />
            <path
              v-for="(seg, i) in pieSegments"
              :key="`pie-${i}`"
              :d="generatePiePath(seg.startAngle, seg.angle)"
              :fill="seg.color"
              class="pie-seg"
              @mouseover="hoveredPoint = { type: 'pie', label: seg.label, percentage: seg.percentage }"
              @mouseout="hoveredPoint = null"
            />
          </svg>
          <div v-if="hoveredPoint?.type === 'pie'" class="pie-center">
            <div class="pie-label">{{ hoveredPoint.label }}</div>
            <div class="pie-pct">{{ hoveredPoint.percentage }}%</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Grid -->
    <div v-else-if="chartData.length" class="charts-grid">
      <!-- Temperature -->
      <div class="panel chart-panel">
        <h3 class="chart-title"><i class="bi bi-thermometer-half"></i> Temperature Over Time</h3>
        <div class="chart-wrap" @wheel="handleWheel" @mousedown="startPan">
          <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" :style="svgTransformStyle">
            <g v-if="showGrid" style="opacity: 0.12">
              <line v-for="i in 10" :key="`t-h-${i}`" :x1="0" :y1="(svgHeight / 10) * i" :x2="svgWidth" :y2="(svgHeight / 10) * i" stroke="white" stroke-width="1" />
              <line v-for="i in 15" :key="`t-v-${i}`" :x1="(svgWidth / 15) * i" :y1="0" :x2="(svgWidth / 15) * i" :y2="svgHeight" stroke="white" stroke-width="1" />
            </g>
            <line :x1="PADDING.left" :y1="PADDING.top" :x2="PADDING.left" :y2="PADDING.top + innerHeight" stroke="#4a5568" stroke-width="2" />
            <line :x1="PADDING.left" :y1="PADDING.top + innerHeight" :x2="PADDING.left + innerWidth" :y2="PADDING.top + innerHeight" stroke="#4a5568" stroke-width="2" />
            <path v-if="selectedVisualization === 'area'" :d="temperatureAreaPath" fill="#ef4444" style="opacity: 0.18" />
            <polyline v-if="selectedVisualization === 'line' || selectedVisualization === 'area'" :points="temperatureLinePoints" fill="none" stroke="#ef4444" stroke-width="2.5" style="filter: drop-shadow(0 0 4px rgba(239, 68, 68, 0.6))" />
            <template v-if="selectedVisualization === 'scatter' || selectedVisualization === 'line' || selectedVisualization === 'area'">
              <circle v-for="p in temperatureSeries" :key="`t-pt-${p.i}`" :cx="p.x" :cy="p.y" :r="isPointSelected('temp', p.i) ? 7 : selectedVisualization === 'scatter' ? 6 : 4" :fill="isPointSelected('temp', p.i) ? '#fbbf24' : '#ef4444'" style="cursor: pointer; transition: all 0.2s ease" @click.ctrl="togglePointSelection('temp', p.i, p.v, null, null, p.t)" @mouseover="hoveredPoint = { type: 'temp', v: p.v, t: p.t }" @mouseout="hoveredPoint = null" />
            </template>
            <template v-if="selectedVisualization === 'bar'">
              <rect v-for="b in tempBars" :key="`t-bar-${b.i}`" :x="b.x" :y="b.y" :width="b.w" :height="b.h" rx="3" :fill="isPointSelected('temp', b.i) ? '#fbbf24' : '#ef4444'" style="cursor: pointer; transition: all 0.2s ease" @click.ctrl="togglePointSelection('temp', b.i, b.v, null, null, b.t)" @mouseover="hoveredPoint = { type: 'temp', v: b.v, t: b.t }" @mouseout="hoveredPoint = null" />
            </template>
          </svg>
          <div v-if="hoveredPoint?.type === 'temp'" class="tooltip tooltip-temp">{{ hoveredPoint.v?.toFixed(2) }}°C<div class="tooltip-sub">{{ formatTs(hoveredPoint.t) }}</div></div>
        </div>
        <div class="zoom-row">
          <button class="btn btn-primary btn-sm" @click="zoomIn"><i class="bi bi-zoom-in"></i></button>
          <button class="btn btn-primary btn-sm" @click="zoomOut"><i class="bi bi-zoom-out"></i></button>
          <button class="btn btn-muted btn-sm" @click="resetView"><i class="bi bi-arrow-counterclockwise"></i></button>
          <span class="zoom-label">{{ (zoomLevel * 100).toFixed(0) }}%</span>
        </div>
      </div>

      <!-- Humidity -->
      <div class="panel chart-panel">
        <h3 class="chart-title"><i class="bi bi-droplet-half"></i> Humidity Over Time</h3>
        <div class="chart-wrap" @wheel="handleWheel" @mousedown="startPan">
          <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" :style="svgTransformStyle">
            <g v-if="showGrid" style="opacity: 0.12">
              <line v-for="i in 10" :key="`h-h-${i}`" :x1="0" :y1="(svgHeight / 10) * i" :x2="svgWidth" :y2="(svgHeight / 10) * i" stroke="white" stroke-width="1" />
              <line v-for="i in 15" :key="`h-v-${i}`" :x1="(svgWidth / 15) * i" :y1="0" :x2="(svgWidth / 15) * i" :y2="svgHeight" stroke="white" stroke-width="1" />
            </g>
            <line :x1="PADDING.left" :y1="PADDING.top" :x2="PADDING.left" :y2="PADDING.top + innerHeight" stroke="#4a5568" stroke-width="2" />
            <line :x1="PADDING.left" :y1="PADDING.top + innerHeight" :x2="PADDING.left + innerWidth" :y2="PADDING.top + innerHeight" stroke="#4a5568" stroke-width="2" />
            <path v-if="selectedVisualization === 'area'" :d="humidityAreaPath" fill="#3b82f6" style="opacity: 0.18" />
            <polyline v-if="selectedVisualization === 'line' || selectedVisualization === 'area'" :points="humidityLinePoints" fill="none" stroke="#3b82f6" stroke-width="2.5" style="filter: drop-shadow(0 0 4px rgba(59, 130, 246, 0.6))" />
            <template v-if="selectedVisualization === 'scatter' || selectedVisualization === 'line' || selectedVisualization === 'area'">
              <circle v-for="p in humiditySeries" :key="`h-pt-${p.i}`" :cx="p.x" :cy="p.y" :r="isPointSelected('hum', p.i) ? 7 : selectedVisualization === 'scatter' ? 6 : 4" :fill="isPointSelected('hum', p.i) ? '#fbbf24' : '#3b82f6'" style="cursor: pointer; transition: all 0.2s ease" @click.ctrl="togglePointSelection('hum', p.i, null, p.v, null, p.t)" @mouseover="hoveredPoint = { type: 'hum', v: p.v, t: p.t }" @mouseout="hoveredPoint = null" />
            </template>
            <template v-if="selectedVisualization === 'bar'">
              <rect v-for="b in humBars" :key="`h-bar-${b.i}`" :x="b.x" :y="b.y" :width="b.w" :height="b.h" rx="3" :fill="isPointSelected('hum', b.i) ? '#fbbf24' : '#3b82f6'" style="cursor: pointer; transition: all 0.2s ease" @click.ctrl="togglePointSelection('hum', b.i, null, b.v, null, b.t)" @mouseover="hoveredPoint = { type: 'hum', v: b.v, t: b.t }" @mouseout="hoveredPoint = null" />
            </template>
          </svg>
          <div v-if="hoveredPoint?.type === 'hum'" class="tooltip tooltip-hum">{{ hoveredPoint.v?.toFixed(2) }}%<div class="tooltip-sub">{{ formatTs(hoveredPoint.t) }}</div></div>
        </div>
        <div class="zoom-row">
          <button class="btn btn-primary btn-sm" @click="zoomIn"><i class="bi bi-zoom-in"></i></button>
          <button class="btn btn-primary btn-sm" @click="zoomOut"><i class="bi bi-zoom-out"></i></button>
          <button class="btn btn-muted btn-sm" @click="resetView"><i class="bi bi-arrow-counterclockwise"></i></button>
          <span class="zoom-label">{{ (zoomLevel * 100).toFixed(0) }}%</span>
        </div>
      </div>

      <!-- Pressure -->
      <div class="panel chart-panel chart-span">
        <h3 class="chart-title"><i class="bi bi-speedometer2"></i> Pressure Over Time</h3>
        <div class="chart-wrap" @wheel="handleWheel" @mousedown="startPan">
          <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" :style="svgTransformStyle">
            <g v-if="showGrid" style="opacity: 0.12">
              <line v-for="i in 10" :key="`p-h-${i}`" :x1="0" :y1="(svgHeight / 10) * i" :x2="svgWidth" :y2="(svgHeight / 10) * i" stroke="white" stroke-width="1" />
              <line v-for="i in 15" :key="`p-v-${i}`" :x1="(svgWidth / 15) * i" :y1="0" :x2="(svgWidth / 15) * i" :y2="svgHeight" stroke="white" stroke-width="1" />
            </g>
            <line :x1="PADDING.left" :y1="PADDING.top" :x2="PADDING.left" :y2="PADDING.top + innerHeight" stroke="#4a5568" stroke-width="2" />
            <line :x1="PADDING.left" :y1="PADDING.top + innerHeight" :x2="PADDING.left + innerWidth" :y2="PADDING.top + innerHeight" stroke="#4a5568" stroke-width="2" />
            <path v-if="selectedVisualization === 'area'" :d="pressureAreaPath" fill="#10b981" style="opacity: 0.18" />
            <polyline v-if="selectedVisualization === 'line' || selectedVisualization === 'area'" :points="pressureLinePoints" fill="none" stroke="#10b981" stroke-width="2.5" style="filter: drop-shadow(0 0 4px rgba(16, 185, 129, 0.6))" />
            <template v-if="selectedVisualization === 'scatter' || selectedVisualization === 'line' || selectedVisualization === 'area'">
              <circle v-for="p in pressureSeries" :key="`p-pt-${p.i}`" :cx="p.x" :cy="p.y" :r="isPointSelected('pres', p.i) ? 7 : selectedVisualization === 'scatter' ? 6 : 4" :fill="isPointSelected('pres', p.i) ? '#fbbf24' : '#10b981'" style="cursor: pointer; transition: all 0.2s ease" @click.ctrl="togglePointSelection('pres', p.i, null, null, p.v, p.t)" @mouseover="hoveredPoint = { type: 'pres', v: p.v, t: p.t }" @mouseout="hoveredPoint = null" />
            </template>
            <template v-if="selectedVisualization === 'bar'">
              <rect v-for="b in presBars" :key="`p-bar-${b.i}`" :x="b.x" :y="b.y" :width="b.w" :height="b.h" rx="3" :fill="isPointSelected('pres', b.i) ? '#fbbf24' : '#10b981'" style="cursor: pointer; transition: all 0.2s ease" @click.ctrl="togglePointSelection('pres', b.i, null, null, b.v, b.t)" @mouseover="hoveredPoint = { type: 'pres', v: b.v, t: b.t }" @mouseout="hoveredPoint = null" />
            </template>
          </svg>
          <div v-if="hoveredPoint?.type === 'pres'" class="tooltip tooltip-pres">{{ (hoveredPoint.v / 1000)?.toFixed(2) }} kPa<div class="tooltip-sub">{{ formatTs(hoveredPoint.t) }}</div></div>
        </div>
        <div class="zoom-row">
          <button class="btn btn-primary btn-sm" @click="zoomIn"><i class="bi bi-zoom-in"></i></button>
          <button class="btn btn-primary btn-sm" @click="zoomOut"><i class="bi bi-zoom-out"></i></button>
          <button class="btn btn-muted btn-sm" @click="resetView"><i class="bi bi-arrow-counterclockwise"></i></button>
          <span class="zoom-label">{{ (zoomLevel * 100).toFixed(0) }}%</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="panel empty">
      <i class="bi bi-inbox empty-icon"></i>
      <p class="empty-text">No data available. Select a device and load data to begin.</p>
    </div>
  </div>
</template>

<style scoped>
.dashboard { background: linear-gradient(135deg, #1a1f3a 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.header { background: linear-gradient(135deg, #2d5a8c 0%, #1a3a52 100%); padding: 24px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1); border: 1px solid #3d5a7f; }
.header-top { display: flex; justify-content: space-between; align-items: center; }
.header-title { color: #fff; margin: 0 0 10px 0; font-size: 32px; font-weight: 800; }
.header-subtitle { color: #a0aec0; margin: 0; }
.live-badge { display: flex; align-items: center; gap: 8px; padding: 8px 14px; background: rgba(34, 197, 94, 0.15); border: 1px solid #22c55e; border-radius: 20px; color: #22c55e; font-weight: 700; font-size: 12px; }
.live-badge.updating { background: rgba(249, 115, 22, 0.15); border-color: #f97316; color: #f97316; }
.pulse { display: inline-block; width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse 1.5s infinite; }
.live-badge.updating .pulse { background: #f97316; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.panel { background: linear-gradient(135deg, #2d3a5f 0%, #1f2948 100%); padding: 20px; border-radius: 12px; border: 1px solid #3d4a6f; box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1); margin-bottom: 20px; }
.controls-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 15px; }
.label { color: #cbd5e0; font-weight: 700; display: block; margin-bottom: 8px; }
.input { width: 100%; padding: 10px 12px; background: linear-gradient(135deg, #1f2948 0%, #16213e 100%); color: #e2e8f0; border: 1px solid #3d4a6f; border-radius: 6px; font-size: 14px; outline: none; transition: all 0.3s ease; }
.input:focus { border-color: #5b9dd9; box-shadow: 0 0 12px rgba(91, 157, 217, 0.3); background: linear-gradient(135deg, #2d3a5f 0%, #1f2948 100%); }
.help { margin-top: 8px; color: #a0aec0; font-size: 12px; }
.load-wrap { display: flex; flex-direction: column; justify-content: flex-end; }
.btn { padding: 10px 16px; border: none; border-radius: 6px; font-weight: 700; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.15s ease; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary { background: #3182ce; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #2563eb; box-shadow: 0 0 14px rgba(49, 130, 206, 0.45); transform: translateY(-1px); }
.btn-muted { background: #718096; color: #fff; }
.btn-muted:hover { background: #4a5568; transform: translateY(-1px); }
.btn-sm { padding: 8px 12px; font-size: 12px; border-radius: 5px; }
.error { margin-top: 15px; padding: 12px; background: #742a2a; border: 1px solid #9b2c2c; border-radius: 6px; color: #fc8181; display: flex; align-items: center; gap: 8px; }
.toolbar { display: flex; gap: 12px; align-items: center; padding: 12px 16px; background: linear-gradient(135deg, #2d3a5f 0%, #1f2948 100%); border: 1px solid #3d4a6f; border-radius: 10px; margin-bottom: 20px; flex-wrap: wrap; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
.tool-btn { padding: 6px 12px; background: #2d3748; color: #a0aec0; border: 1px solid #4a5568; border-radius: 5px; cursor: pointer; font-size: 12px; transition: all 0.2s ease; display: flex; align-items: center; gap: 6px; }
.tool-btn:hover { background: #3d4a5c; color: #e2e8f0; }
.tool-btn.active { background: #3182ce; color: #fff; border-color: #3182ce; }
.toolbar-info { font-size: 12px; color: #718096; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 15px; margin-bottom: 20px; }
.stat { padding: 18px; border-radius: 10px; color: #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.25); transition: all 0.2s ease; }
.stat:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.35); }
.stat-temp { background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); }
.stat-hum { background: linear-gradient(135deg, #0dcaf0 0%, #0d6efd 100%); }
.stat-pres { background: linear-gradient(135deg, #20c997 0%, #198754 100%); }
.stat-count { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); }
.stat-selected { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
.stat-label { font-size: 14px; opacity: 0.9; margin-bottom: 8px; font-weight: 700; }
.stat-value { font-size: 30px; font-weight: 900; margin-bottom: 8px; }
.stat-sub { font-size: 12px; opacity: 0.85; }
.stat-row { display: flex; gap: 12px; font-size: 12px; flex-wrap: wrap; }
.stat-row-item { background: rgba(0,0,0,0.2); padding: 4px 8px; border-radius: 4px; }
.viz-panel { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.viz-title { color: #a0aec0; font-weight: 800; margin-right: 10px; }
.viz-btn { padding: 10px 14px; background: #2d3748; color: #fff; border: 1px solid #4a5568; border-radius: 8px; cursor: pointer; font-size: 13px; display: inline-flex; align-items: center; gap: 8px; transition: all 0.15s ease; }
.viz-btn:hover { box-shadow: 0 0 12px rgba(49, 130, 206, 0.45); transform: translateY(-1px); }
.viz-btn.active { background: #3182ce; border: 2px solid #63b3ed; font-weight: 800; }
.viz-num { background: rgba(0,0,0,0.25); padding: 2px 8px; border-radius: 4px; font-weight: 900; font-size: 12px; }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(560px, 1fr)); gap: 20px; }
.chart-panel { transition: box-shadow 0.2s ease; }
.chart-panel:hover { box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
.chart-span { grid-column: 1 / -1; }
.chart-title { color: #e2e8f0; margin: 0 0 12px 0; font-size: 16px; font-weight: 800; }
.chart-wrap { height: 350px; background: linear-gradient(135deg, #0f1419 0%, #1a1f3a 100%); border-radius: 8px; overflow: hidden; position: relative; cursor: grab; border: 1px solid #2d3a5f; }
.chart-wrap:active { cursor: grabbing; }
.tooltip { position: absolute; bottom: 18px; left: 18px; background: rgba(0,0,0,0.82); padding: 10px 14px; border-radius: 6px; font-weight: 800; border: 1px solid #4a5568; animation: slideIn 0.2s ease; }
@keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.tooltip-sub { font-size: 11px; opacity: 0.8; margin-top: 4px; font-weight: 600; }
.tooltip-temp { color: #ef4444; border-color: rgba(239, 68, 68, 0.7); }
.tooltip-hum { color: #3b82f6; border-color: rgba(59, 130, 246, 0.7); }
.tooltip-pres { color: #10b981; border-color: rgba(16, 185, 129, 0.7); }
.zoom-row { display: flex; gap: 10px; margin-top: 14px; justify-content: center; align-items: center; flex-wrap: wrap; }
.zoom-label { color: #a0aec0; font-size: 12px; font-weight: 700; }
.empty { padding: 60px; text-align: center; }
.empty-icon { font-size: 48px; color: #4a5568; display: block; margin-bottom: 18px; }
.empty-text { color: #a0aec0; font-size: 18px; margin: 0; }
.pie-wrap { position: relative; width: 300px; height: 300px; margin: 0 auto; display: flex; align-items: center; justify-content: center; }
.pie-svg { width: 100%; height: 100%; }
.pie-seg { opacity: 0.85; cursor: pointer; transition: opacity 0.15s ease, transform 0.15s ease; }
.pie-seg:hover { opacity: 1; filter: brightness(1.1); }
.pie-center { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #fff; }
.pie-label { font-size: 14px; opacity: 0.85; font-weight: 700; }
.pie-pct { font-size: 22px; font-weight: 900; }
</style> 