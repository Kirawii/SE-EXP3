<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as landmarkApi from '@/api/landmarks';
import type { Landmark } from '@/types';

const router = useRouter();
const list = ref<Landmark[]>([]);
const loading = ref(false);

async function refresh() {
  loading.value = true;
  try {
    list.value = await landmarkApi.listMine();
  } finally {
    loading.value = false;
  }
}

async function onDelete(row: Landmark) {
  try {
    await ElMessageBox.confirm(`确认删除地标"${row.name}"?`, '删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    });
  } catch {
    return;
  }
  await landmarkApi.deleteLandmark(row.id);
  ElMessage.success('已删除');
  await refresh();
}

function statusType(s: Landmark['status']): 'success' | 'warning' | 'danger' {
  return s === 'APPROVED' ? 'success' : s === 'PENDING' ? 'warning' : 'danger';
}

function statusText(s: Landmark['status']): string {
  return ({ APPROVED: '已审核', PENDING: '待审核', REJECTED: '已驳回' } as const)[s];
}

onMounted(() => {
  void refresh();
});
</script>

<template>
  <div class="page">
    <div class="header-row">
      <h2>我的地标</h2>
      <el-button @click="refresh" :loading="loading">刷新</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="list"
      class="card-shadow"
      empty-text="尚未创建地标,前往地图页面新建"
      stripe
    >
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
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="200">
        <template #default="{ row }">
          <span class="muted">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" link @click="router.push(`/landmarks/${row.id}`)">详情</el-button>
          <el-button size="small" link type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header-row h2 {
  margin: 0;
  font-size: 18px;
}
.link {
  color: #409eff;
}
</style>
