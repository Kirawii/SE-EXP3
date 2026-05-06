<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, reactive } from 'vue';
import L from 'leaflet';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import * as geoApi from '@/api/geo';
import * as landmarkApi from '@/api/landmarks';
import LandmarkForm from '@/components/LandmarkForm.vue';
import type { LandmarkCreateIn, NearbyHit } from '@/types';

// 北京中心
const DEFAULT_CENTER: [number, number] = [39.908, 116.397];
const DEFAULT_ZOOM = 11;

// leaflet 默认 marker 图标在打包后路径丢失,这里显式指定
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

const router = useRouter();
const auth = useAuthStore();

const mapEl = ref<HTMLDivElement>();
const radiusKm = ref(20);
const hits = ref<NearbyHit[]>([]);
const loading = ref(false);

const dialogOpen = ref(false);
const submitting = ref(false);
const formData = reactive<LandmarkCreateIn>({
  name: '',
  category: '',
  description: '',
  image_url: '',
  lng: DEFAULT_CENTER[1],
  lat: DEFAULT_CENTER[0],
});

let map: L.Map | null = null;
let markerLayer: L.LayerGroup | null = null;

function fmtDistance(km: number): string {
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(2)} km`;
}

async function refresh() {
  if (!map) return;
  const center = map.getCenter();
  loading.value = true;
  try {
    const list = await geoApi.nearby({
      lng: center.lng,
      lat: center.lat,
      radius_km: Math.min(radiusKm.value, 50),
      limit: 200,
    });
    hits.value = list;
    drawMarkers(list);
  } finally {
    loading.value = false;
  }
}

function drawMarkers(list: NearbyHit[]) {
  if (!map || !markerLayer) return;
  markerLayer.clearLayers();
  for (const h of list) {
    const m = L.marker([h.lat, h.lng]).bindPopup(
      `<strong>${escapeHtml(h.name)}</strong><br/>` +
        `<span style="color:#909399">${escapeHtml(h.category)} · ${fmtDistance(h.distance_km)}</span><br/>` +
        `<a href="#/landmarks/${encodeURIComponent(h.id)}" data-id="${encodeURIComponent(h.id)}" class="popup-link">查看详情 →</a>`,
    );
    m.on('popupopen', () => {
      const el = document.querySelector<HTMLAnchorElement>(`a.popup-link[data-id="${encodeURIComponent(h.id)}"]`);
      el?.addEventListener('click', (e) => {
        e.preventDefault();
        router.push(`/landmarks/${h.id}`);
      });
    });
    m.addTo(markerLayer);
  }
}

function escapeHtml(s: string): string {
  return s.replace(/[<>&"']/g, (c) => ({
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    '"': '&quot;',
    "'": '&#39;',
  })[c] as string);
}

function openCreate() {
  if (!auth.isAuthed) {
    ElMessageBox.confirm('需要先登录才能创建地标。', '请登录', { type: 'info' })
      .then(() => router.push('/login'))
      .catch(() => {});
    return;
  }
  if (!map) return;
  const c = map.getCenter();
  formData.name = '';
  formData.category = '';
  formData.description = '';
  formData.image_url = '';
  formData.lng = +c.lng.toFixed(6);
  formData.lat = +c.lat.toFixed(6);
  dialogOpen.value = true;
}

async function onCreateSubmit(payload: LandmarkCreateIn) {
  submitting.value = true;
  try {
    await landmarkApi.createLandmark({
      ...payload,
      description: payload.description || '',
      image_url: payload.image_url || null,
    });
    ElMessage.success('地标已创建');
    dialogOpen.value = false;
    await refresh();
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  if (!mapEl.value) return;
  map = L.map(mapEl.value).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors',
  }).addTo(map);
  markerLayer = L.layerGroup().addTo(map);
  map.on('moveend', () => void refresh());
  void refresh();
});

onBeforeUnmount(() => {
  map?.remove();
  map = null;
});
</script>

<template>
  <div class="map-view">
    <div class="toolbar">
      <div class="left">
        <span class="muted">半径</span>
        <el-input-number
          v-model="radiusKm"
          :min="1"
          :max="50"
          :step="1"
          size="small"
          style="width: 110px"
          @change="refresh"
        />
        <span class="muted">km · 共 {{ hits.length }} 个地标</span>
      </div>
      <div class="right">
        <el-button :icon="undefined" :loading="loading" size="small" @click="refresh">
          刷新
        </el-button>
        <el-button type="primary" size="small" @click="openCreate">
          在视图中心创建地标
        </el-button>
      </div>
    </div>
    <div ref="mapEl" class="map"></div>

    <el-dialog v-model="dialogOpen" title="创建地标" width="520px">
      <LandmarkForm
        v-model="formData"
        :loading="submitting"
        submit-text="创建"
        @submit="onCreateSubmit"
      />
    </el-dialog>
  </div>
</template>

<style scoped>
.map-view {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  gap: 16px;
}
.left,
.right {
  display: flex;
  gap: 8px;
  align-items: center;
}
.map {
  flex: 1;
  width: 100%;
  min-height: calc(100vh - var(--header-h) - 48px);
}
</style>
