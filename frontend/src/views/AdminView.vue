<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as adminApi from '@/api/admin';
import { useAuthStore } from '@/stores/auth';
import type { Landmark, User } from '@/types';

const auth = useAuthStore();
const tab = ref('review');

const pending = ref<Landmark[]>([]);
const pendingLoading = ref(false);
const users = ref<User[]>([]);
const usersLoading = ref(false);

async function loadPending() {
  pendingLoading.value = true;
  try {
    pending.value = await adminApi.listLandmarksByStatus('PENDING');
  } finally {
    pendingLoading.value = false;
  }
}

async function review(lm: Landmark, action: 'approve' | 'reject') {
  await adminApi.reviewLandmark(lm.id, action);
  ElMessage.success(action === 'approve' ? '已通过' : '已驳回');
  await loadPending();
}

async function loadUsers() {
  usersLoading.value = true;
  try {
    users.value = await adminApi.listUsers();
  } finally {
    usersLoading.value = false;
  }
}

async function toggleUser(u: User) {
  const disable = !u.disabled;
  try {
    await ElMessageBox.confirm(
      `确认${disable ? '禁用' : '启用'}用户「${u.username}」?`,
      disable ? '禁用用户' : '启用用户',
      { type: 'warning' },
    );
  } catch {
    return;
  }
  if (disable) await adminApi.disableUser(u.id);
  else await adminApi.enableUser(u.id);
  ElMessage.success('操作成功');
  await loadUsers();
}

async function exportCsv() {
  const blob = await adminApi.exportLandmarksCsv();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'landmarks.csv';
  a.click();
  URL.revokeObjectURL(url);
}

onMounted(() => {
  void loadPending();
  void loadUsers();
});
</script>

<template>
  <div class="page">
    <div class="header-row">
      <h2>管理后台</h2>
      <el-button type="primary" plain @click="exportCsv">导出地标 CSV</el-button>
    </div>

    <el-tabs v-model="tab" class="card-shadow tabs">
      <el-tab-pane label="地标审核" name="review">
        <el-empty v-if="!pendingLoading && !pending.length" description="没有待审核的地标" />
        <el-table v-else v-loading="pendingLoading" :data="pending" stripe>
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column prop="category" label="类别" width="120" />
          <el-table-column label="坐标" width="200">
            <template #default="{ row }">
              <span class="muted">{{ row.lng.toFixed(4) }}, {{ row.lat.toFixed(4) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="owner_id" label="提交者" width="100" />
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="review(row, 'approve')">通过</el-button>
              <el-button size="small" type="danger" @click="review(row, 'reject')">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="用户管理" name="users">
        <el-table v-loading="usersLoading" :data="users" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户名" min-width="140" />
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="row.role === 'ADMIN' ? 'danger' : 'info'" size="small">
                {{ row.role }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.disabled ? 'warning' : 'success'" size="small">
                {{ row.disabled ? '已禁用' : '正常' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                v-if="row.role !== 'ADMIN' && row.id !== auth.user?.id"
                size="small"
                :type="row.disabled ? 'success' : 'danger'"
                link
                @click="toggleUser(row)"
              >
                {{ row.disabled ? '启用' : '禁用' }}
              </el-button>
              <span v-else class="muted">—</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
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
.tabs {
  padding: 8px 20px 20px;
}
</style>
