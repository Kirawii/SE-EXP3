<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { searchLandmarks } from '@/api/landmarks';
import type { Landmark } from '@/types';

const router = useRouter();
const keyword = ref('');
const category = ref('');
const list = ref<Landmark[]>([]);
const loading = ref(false);

async function run() {
  loading.value = true;
  try {
    list.value = await searchLandmarks({
      q: keyword.value.trim() || undefined,
      category: category.value.trim() || undefined,
      limit: 200,
    });
  } finally {
    loading.value = false;
  }
}

function reset() {
  keyword.value = '';
  category.value = '';
  void run();
}

onMounted(() => void run());
</script>

<template>
  <div class="page">
    <h2>探索地标</h2>
    <div class="filters card-shadow">
      <el-input
        v-model="keyword"
        placeholder="按名称关键字搜索"
        clearable
        style="width: 240px"
        @keyup.enter="run"
      />
      <el-input
        v-model="category"
        placeholder="按类别精确筛选"
        clearable
        style="width: 200px"
        @keyup.enter="run"
      />
      <el-button type="primary" :loading="loading" @click="run">检索</el-button>
      <el-button @click="reset">重置</el-button>
      <span class="muted">共 {{ list.length }} 个结果</span>
    </div>

    <el-empty v-if="!loading && !list.length" description="没有匹配的地标" />

    <div v-else class="grid">
      <div
        v-for="lm in list"
        :key="lm.id"
        class="card-shadow item"
        @click="router.push(`/landmarks/${lm.id}`)"
      >
        <img v-if="lm.image_url" :src="lm.image_url" class="thumb" alt="" />
        <div v-else class="thumb thumb--empty">无图</div>
        <div class="body">
          <div class="name">{{ lm.name }}</div>
          <el-tag size="small" effect="plain">{{ lm.category }}</el-tag>
          <p class="desc muted">{{ lm.description || '暂无描述' }}</p>
          <div class="coord muted">{{ lm.lng.toFixed(4) }}, {{ lm.lat.toFixed(4) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
h2 {
  font-size: 18px;
  margin: 0 0 16px;
}
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.item {
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.12s, box-shadow 0.12s;
}
.item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.12);
}
.thumb {
  width: 100%;
  height: 140px;
  object-fit: cover;
  display: block;
}
.thumb--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
  color: #c0c4cc;
  font-size: 13px;
}
.body {
  padding: 14px;
}
.name {
  font-weight: 600;
  margin-bottom: 8px;
}
.desc {
  font-size: 13px;
  margin: 10px 0 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.coord {
  font-size: 12px;
}
</style>
