<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { listFavorites, removeFavorite } from '@/api/social';
import type { Landmark } from '@/types';

const router = useRouter();
const list = ref<Landmark[]>([]);
const loading = ref(false);

async function refresh() {
  loading.value = true;
  try {
    list.value = await listFavorites();
  } finally {
    loading.value = false;
  }
}

async function onRemove(lm: Landmark) {
  await removeFavorite(lm.id);
  ElMessage.success('已取消收藏');
  await refresh();
}

onMounted(() => void refresh());
</script>

<template>
  <div class="page">
    <h2>我的收藏</h2>
    <el-empty v-if="!loading && !list.length" description="还没有收藏任何地标" />
    <el-table v-else v-loading="loading" :data="list" class="card-shadow" stripe>
      <el-table-column prop="name" label="名称" min-width="160">
        <template #default="{ row }">
          <router-link :to="`/landmarks/${row.id}`" class="link">{{ row.name }}</router-link>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="类别" width="140" />
      <el-table-column label="坐标" width="220">
        <template #default="{ row }">
          <span class="muted">{{ row.lng.toFixed(4) }}, {{ row.lat.toFixed(4) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" link @click="router.push(`/landmarks/${row.id}`)">详情</el-button>
          <el-button size="small" link type="danger" @click="onRemove(row)">取消收藏</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
h2 {
  font-size: 18px;
  margin: 0 0 16px;
}
.link {
  color: #409eff;
}
</style>
