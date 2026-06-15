<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, reactive } from 'vue';
import L from 'leaflet';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import * as geoApi from '@/api/geo';
import * as landmarkApi from '@/api/landmarks';
import { planDrive, type DriveStyle } from '@/api/route';
import { addBaseLayers } from '@/map/tiles';
import LandmarkForm from '@/components/LandmarkForm.vue';
import type { LandmarkCreateIn, NearbyHit, RecommendHit } from '@/types';

// 默认北京中心
const DEFAULT_CENTER: [number, number] = [39.908, 116.397];
const DEFAULT_ZOOM = 11;
const VIEW_STORAGE_KEY = 'map:last_view';

// 常用城市快选 [纬度, 经度]
const CITIES: { name: string; center: [number, number] }[] = [
  { name: '北京', center: [39.908, 116.397] },
  { name: '上海', center: [31.230, 121.474] },
  { name: '广州', center: [23.129, 113.264] },
  { name: '深圳', center: [22.543, 114.058] },
  { name: '成都', center: [30.572, 104.067] },
  { name: '西安', center: [34.342, 108.940] },
  { name: '杭州', center: [30.274, 120.155] },
  { name: '武汉', center: [30.593, 114.305] },
];

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
const queryMode = ref<'radius' | 'box'>('radius');
const radiusKm = ref(20);
const widthKm = ref(30);
const heightKm = ref(30);
const hits = ref<NearbyHit[]>([]);
const loading = ref(false);

// 位置切换
const selectedCity = ref<string>('');
const locating = ref(false);

// 工具面板：测距 / 路线 / 推荐
const tool = ref<'dist' | 'route' | 'recommend'>('dist');

// 距离测量(GEODIST)
const distA = ref<string>('');
const distB = ref<string>('');
const distResult = ref<number | null>(null);

// 路径规划(天地图驾车)
const routeFrom = ref<string>('');
const routeTo = ref<string>('');
const routeStyle = ref<DriveStyle>('0');
const routePlanning = ref(false);
const routeInfo = ref<{ distance_km: number; duration_min: number } | null>(null);

// 附近商家推荐
const recommendCategory = ref<string>('');
const recommendLoading = ref(false);
const recommendList = ref<RecommendHit[]>([]);

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
let routeLayer: L.LayerGroup | null = null;

function fmtDistance(km: number): string {
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(2)} km`;
}

/**
 * Leaflet 横向可无限滚动，getCenter().lng 可能超出 ±180；纬度也可能
 * 漂出 Web Mercator 的 ±85.05 上限。这里把经度环绕归一、纬度夹紧。
 */
function wrappedCenter(): { lng: number; lat: number } {
  if (!map) return { lng: 0, lat: 0 };
  const c = map.wrapLatLng(map.getCenter());
  const lat = Math.max(-85.05, Math.min(85.05, c.lat));
  return { lng: +c.lng.toFixed(6), lat: +lat.toFixed(6) };
}

async function refresh() {
  if (!map) return;
  const center = wrappedCenter();
  loading.value = true;
  try {
    const list =
      queryMode.value === 'radius'
        ? await geoApi.nearby({
            lng: center.lng,
            lat: center.lat,
            radius_km: Math.min(radiusKm.value, 50),
            limit: 200,
          })
        : await geoApi.box({
            lng: center.lng,
            lat: center.lat,
            width_km: Math.min(widthKm.value, 200),
            height_km: Math.min(heightKm.value, 200),
            limit: 200,
          });
    hits.value = list;
    drawMarkers(list);
    // 清掉已不在结果集中的距离测量选择
    const ids = new Set(list.map((h) => h.id));
    if (distA.value && !ids.has(distA.value)) distA.value = '';
    if (distB.value && !ids.has(distB.value)) distB.value = '';
    distResult.value = null;
  } finally {
    loading.value = false;
  }
}

async function computeDistance() {
  if (!distA.value || !distB.value || distA.value === distB.value) {
    ElMessage.warning('请选择两个不同的地标');
    return;
  }
  const res = await geoApi.distance(distA.value, distB.value);
  distResult.value = res.distance_km;
}

function hitById(id: string): NearbyHit | undefined {
  return hits.value.find((h) => h.id === id);
}

async function planRoute() {
  const a = hitById(routeFrom.value);
  const b = hitById(routeTo.value);
  if (!a || !b || a.id === b.id) {
    ElMessage.warning('请选择两个不同的地标作为起点与终点');
    return;
  }
  routePlanning.value = true;
  try {
    const plan = await planDrive([a.lng, a.lat], [b.lng, b.lat], routeStyle.value);
    routeInfo.value = { distance_km: plan.distance_km, duration_min: plan.duration_min };
    drawRoute(plan.points, [a.lat, a.lng], [b.lat, b.lng]);
  } catch (e) {
    ElMessage.error((e as Error).message || '路径规划失败');
  } finally {
    routePlanning.value = false;
  }
}

function drawRoute(
  points: [number, number][],
  start: [number, number],
  end: [number, number],
) {
  if (!map) return;
  if (!routeLayer) routeLayer = L.layerGroup().addTo(map);
  routeLayer.clearLayers();
  const line = L.polyline(points, { color: '#409eff', weight: 5, opacity: 0.8 });
  L.marker(start).bindPopup('起点').addTo(routeLayer);
  L.marker(end).bindPopup('终点').addTo(routeLayer);
  line.addTo(routeLayer);
  map.fitBounds(line.getBounds(), { padding: [40, 40] });
}

function clearRoute() {
  routeLayer?.clearLayers();
  routeInfo.value = null;
  routeFrom.value = '';
  routeTo.value = '';
}

async function loadRecommend() {
  if (!map) return;
  const center = wrappedCenter();
  recommendLoading.value = true;
  try {
    recommendList.value = await geoApi.recommend({
      lng: center.lng,
      lat: center.lat,
      radius_km: Math.min(radiusKm.value, 50),
      category: recommendCategory.value.trim() || undefined,
      limit: 10,
    });
  } finally {
    recommendLoading.value = false;
  }
}

function focusHit(h: RecommendHit) {
  map?.setView([h.lat, h.lng], 16);
}

function flyToCity(name: string) {
  const city = CITIES.find((c) => c.name === name);
  if (city && map) map.setView(city.center, 12);
}

function locateMe() {
  if (!navigator.geolocation) {
    ElMessage.warning('当前浏览器不支持定位');
    return;
  }
  locating.value = true;
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      locating.value = false;
      selectedCity.value = '';
      map?.setView([pos.coords.latitude, pos.coords.longitude], 13);
    },
    () => {
      locating.value = false;
      ElMessage.error('定位失败，请检查浏览器定位权限');
    },
    { enableHighAccuracy: true, timeout: 8000 },
  );
}

function loadSavedView(): { center: [number, number]; zoom: number } {
  try {
    const raw = localStorage.getItem(VIEW_STORAGE_KEY);
    if (raw) {
      const v = JSON.parse(raw);
      if (Array.isArray(v.center) && typeof v.zoom === 'number') {
        return { center: v.center, zoom: v.zoom };
      }
    }
  } catch {
    /* 忽略损坏的缓存 */
  }
  return { center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM };
}

function saveView() {
  if (!map) return;
  const c = wrappedCenter();
  localStorage.setItem(
    VIEW_STORAGE_KEY,
    JSON.stringify({ center: [c.lat, c.lng], zoom: map.getZoom() }),
  );
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
  const c = wrappedCenter();
  formData.name = '';
  formData.category = '';
  formData.description = '';
  formData.image_url = '';
  formData.lng = c.lng;
  formData.lat = c.lat;
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
  const saved = loadSavedView();
  map = L.map(mapEl.value).setView(saved.center, saved.zoom);
  addBaseLayers(map);
  markerLayer = L.layerGroup().addTo(map);
  map.on('moveend', () => {
    saveView();
    void refresh();
  });
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
        <el-radio-group v-model="queryMode" size="small" @change="refresh">
          <el-radio-button value="radius">圆形</el-radio-button>
          <el-radio-button value="box">矩形</el-radio-button>
        </el-radio-group>

        <template v-if="queryMode === 'radius'">
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
          <span class="muted">km</span>
        </template>
        <template v-else>
          <span class="muted">宽</span>
          <el-input-number v-model="widthKm" :min="1" :max="200" size="small" style="width: 100px" @change="refresh" />
          <span class="muted">高</span>
          <el-input-number v-model="heightKm" :min="1" :max="200" size="small" style="width: 100px" @change="refresh" />
          <span class="muted">km</span>
        </template>

        <span class="muted">· 共 {{ hits.length }} 个地标</span>
      </div>
      <div class="right">
        <el-select
          v-model="selectedCity"
          placeholder="切换城市"
          size="small"
          clearable
          style="width: 120px"
          @change="flyToCity"
        >
          <el-option v-for="c in CITIES" :key="c.name" :label="c.name" :value="c.name" />
        </el-select>
        <el-button :loading="locating" size="small" @click="locateMe">定位</el-button>
        <el-button :loading="loading" size="small" @click="refresh">刷新</el-button>
        <el-button type="primary" size="small" @click="openCreate">
          在视图中心创建地标
        </el-button>
      </div>
    </div>

    <div class="tool-bar">
      <el-radio-group v-model="tool" size="small">
        <el-radio-button value="dist">测距</el-radio-button>
        <el-radio-button value="route">路线规划</el-radio-button>
        <el-radio-button value="recommend">商家推荐</el-radio-button>
      </el-radio-group>

      <!-- 测距：GEODIST -->
      <template v-if="tool === 'dist'">
        <el-select v-model="distA" placeholder="地标 A" size="small" filterable style="width: 150px">
          <el-option v-for="h in hits" :key="h.id" :label="h.name" :value="h.id" />
        </el-select>
        <span class="muted">→</span>
        <el-select v-model="distB" placeholder="地标 B" size="small" filterable style="width: 150px">
          <el-option v-for="h in hits" :key="h.id" :label="h.name" :value="h.id" />
        </el-select>
        <el-button size="small" @click="computeDistance">计算</el-button>
        <el-tag v-if="distResult !== null" type="success">{{ distResult.toFixed(3) }} km</el-tag>
      </template>

      <!-- 路线规划：天地图驾车 -->
      <template v-else-if="tool === 'route'">
        <el-select v-model="routeFrom" placeholder="起点" size="small" filterable style="width: 140px">
          <el-option v-for="h in hits" :key="h.id" :label="h.name" :value="h.id" />
        </el-select>
        <span class="muted">→</span>
        <el-select v-model="routeTo" placeholder="终点" size="small" filterable style="width: 140px">
          <el-option v-for="h in hits" :key="h.id" :label="h.name" :value="h.id" />
        </el-select>
        <el-select v-model="routeStyle" size="small" style="width: 110px">
          <el-option label="最快路线" value="0" />
          <el-option label="最短路线" value="1" />
          <el-option label="避开高速" value="2" />
        </el-select>
        <el-button type="primary" size="small" :loading="routePlanning" @click="planRoute">规划</el-button>
        <el-button size="small" @click="clearRoute">清除</el-button>
        <el-tag v-if="routeInfo" type="success">
          {{ routeInfo.distance_km }} km · 约 {{ routeInfo.duration_min }} 分钟
        </el-tag>
      </template>

      <!-- 商家推荐 -->
      <template v-else>
        <span class="muted">以地图中心 {{ Math.min(radiusKm, 50) }} km 内</span>
        <el-input v-model="recommendCategory" placeholder="类别(可选)" size="small" clearable style="width: 140px" />
        <el-button type="primary" size="small" :loading="recommendLoading" @click="loadRecommend">
          获取推荐
        </el-button>
        <span v-if="recommendList.length" class="muted">共 {{ recommendList.length }} 家</span>
      </template>
    </div>

    <div class="map-wrap">
      <div ref="mapEl" class="map"></div>

      <!-- 推荐结果浮层 -->
      <div v-if="tool === 'recommend' && recommendList.length" class="recommend-panel card-shadow">
        <div class="rp-title">推荐 · 距离与热度综合排序</div>
        <ol class="rp-list">
          <li v-for="(h, i) in recommendList" :key="h.id" class="rp-item" @click="focusHit(h)">
            <span class="rp-rank">{{ i + 1 }}</span>
            <div class="rp-main">
              <div class="rp-name">{{ h.name }}</div>
              <div class="rp-meta muted">
                {{ h.category }} · {{ h.distance_km.toFixed(2) }} km · ♥ {{ h.popularity }}
              </div>
            </div>
            <router-link :to="`/landmarks/${h.id}`" class="rp-link" @click.stop>详情</router-link>
          </li>
        </ol>
      </div>
    </div>

    <el-dialog v-model="dialogOpen" title="创建地标" width="520px">
      <LandmarkForm
        v-if="dialogOpen"
        :initial="formData"
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
  flex-wrap: wrap;
}
.tool-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 24px;
  background: #fafbfc;
  border-bottom: 1px solid #ebeef5;
  flex-wrap: wrap;
}
.map-wrap {
  position: relative;
  flex: 1;
  display: flex;
}
.map {
  flex: 1;
  width: 100%;
  min-height: calc(100vh - var(--header-h) - 96px);
}
.recommend-panel {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 280px;
  max-height: calc(100% - 24px);
  overflow-y: auto;
  background: #fff;
  border-radius: 8px;
  z-index: 1000;
  padding: 12px 0;
}
.rp-title {
  font-size: 13px;
  font-weight: 600;
  padding: 0 14px 10px;
  border-bottom: 1px solid #f0f2f5;
}
.rp-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.rp-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
}
.rp-item:hover {
  background: #f5f7fa;
}
.rp-rank {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.rp-main {
  flex: 1;
  min-width: 0;
}
.rp-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rp-meta {
  font-size: 12px;
}
.rp-link {
  font-size: 12px;
  color: #409eff;
  flex-shrink: 0;
}
</style>
