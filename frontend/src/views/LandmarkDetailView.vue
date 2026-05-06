<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch, reactive } from 'vue';
import L from 'leaflet';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as landmarkApi from '@/api/landmarks';
import * as geoApi from '@/api/geo';
import { useAuthStore } from '@/stores/auth';
import LandmarkForm from '@/components/LandmarkForm.vue';
import type { Landmark, LandmarkCreateIn } from '@/types';

const props = defineProps<{ id: string }>();
const router = useRouter();
const auth = useAuthStore();

const landmark = ref<Landmark | null>(null);
const loading = ref(false);
const geohash = ref<string>('');

const isOwner = computed(() => !!landmark.value && landmark.value.owner_id === auth.user?.id);

const editing = ref(false);
const submitting = ref(false);
const formData = reactive<LandmarkCreateIn>({
  name: '',
  category: '',
  description: '',
  image_url: '',
  lng: 0,
  lat: 0,
});

const mapEl = ref<HTMLDivElement>();
let map: L.Map | null = null;
let marker: L.Marker | null = null;

async function load() {
  loading.value = true;
  try {
    const [lm, hash] = await Promise.all([
      landmarkApi.getLandmark(props.id),
      geoApi.geohash(props.id).catch(() => ({ id: props.id, geohash: '' })),
    ]);
    landmark.value = lm;
    geohash.value = hash.geohash;
  } finally {
    loading.value = false;
  }
}

function startEdit() {
  if (!landmark.value) return;
  Object.assign(formData, {
    name: landmark.value.name,
    category: landmark.value.category,
    description: landmark.value.description,
    image_url: landmark.value.image_url || '',
    lng: landmark.value.lng,
    lat: landmark.value.lat,
  });
  editing.value = true;
}

async function onUpdate(payload: LandmarkCreateIn) {
  if (!landmark.value) return;
  submitting.value = true;
  try {
    landmark.value = await landmarkApi.updateLandmark(landmark.value.id, {
      ...payload,
      image_url: payload.image_url || null,
    });
    ElMessage.success('已更新');
    editing.value = false;
  } finally {
    submitting.value = false;
  }
}

async function onDelete() {
  if (!landmark.value) return;
  try {
    await ElMessageBox.confirm(`确认删除"${landmark.value.name}"?`, '删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    });
  } catch {
    return;
  }
  await landmarkApi.deleteLandmark(landmark.value.id);
  ElMessage.success('已删除');
  router.replace('/landmarks');
}

watch(landmark, (lm) => {
  if (!lm || !mapEl.value) return;
  if (!map) {
    map = L.map(mapEl.value).setView([lm.lat, lm.lng], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors',
    }).addTo(map);
  } else {
    map.setView([lm.lat, lm.lng], 14);
  }
  if (marker) marker.remove();
  marker = L.marker([lm.lat, lm.lng]).bindPopup(lm.name).addTo(map);
});

onMounted(() => void load());
onBeforeUnmount(() => {
  map?.remove();
  map = null;
});
</script>

<template>
  <div class="page" v-loading="loading">
    <template v-if="landmark">
      <div class="header-row">
        <div>
          <h2>{{ landmark.name }}</h2>
          <div class="meta">
            <el-tag size="small">{{ landmark.category }}</el-tag>
            <span class="muted">坐标 {{ landmark.lng.toFixed(6) }}, {{ landmark.lat.toFixed(6) }}</span>
            <span v-if="geohash" class="muted">Geohash {{ geohash }}</span>
          </div>
        </div>
        <div v-if="isOwner" class="actions">
          <el-button @click="startEdit">编辑</el-button>
          <el-button type="danger" @click="onDelete">删除</el-button>
        </div>
      </div>

      <div class="grid">
        <div class="card-shadow info">
          <h3>简介</h3>
          <p v-if="landmark.description" class="desc">{{ landmark.description }}</p>
          <p v-else class="muted">未填写描述</p>
          <img v-if="landmark.image_url" :src="landmark.image_url" alt="" class="cover" />
          <dl class="kv">
            <dt>状态</dt>
            <dd>{{ landmark.status }}</dd>
            <dt>创建</dt>
            <dd>{{ new Date(landmark.created_at).toLocaleString('zh-CN') }}</dd>
            <dt>更新</dt>
            <dd>{{ new Date(landmark.updated_at).toLocaleString('zh-CN') }}</dd>
          </dl>
        </div>
        <div ref="mapEl" class="map card-shadow"></div>
      </div>
    </template>

    <el-dialog v-model="editing" title="编辑地标" width="520px">
      <LandmarkForm
        v-model="formData"
        :loading="submitting"
        submit-text="保存"
        @submit="onUpdate"
      />
    </el-dialog>
  </div>
</template>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 16px;
}
.header-row h2 {
  margin: 0 0 6px;
}
.meta {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 13px;
  flex-wrap: wrap;
}
.actions {
  display: flex;
  gap: 8px;
}
.grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
}
.info {
  padding: 20px;
}
.info h3 {
  margin: 0 0 12px;
  font-size: 15px;
}
.desc {
  white-space: pre-wrap;
  line-height: 1.6;
  margin: 0 0 16px;
}
.cover {
  max-width: 100%;
  border-radius: 4px;
  margin-bottom: 16px;
}
.kv {
  margin: 0;
  display: grid;
  grid-template-columns: 64px 1fr;
  row-gap: 6px;
  font-size: 13px;
}
.kv dt {
  color: #909399;
}
.kv dd {
  margin: 0;
}
.map {
  min-height: 400px;
}
@media (max-width: 720px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
