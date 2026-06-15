<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import * as authApi from '@/api/auth';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const loading = ref(false);
const saving = ref(false);
const form = reactive({ nickname: '', avatar: '' });

async function load() {
  loading.value = true;
  try {
    const u = await authApi.me();
    auth.user = u;
    form.nickname = u.nickname || '';
    form.avatar = u.avatar || '';
  } finally {
    loading.value = false;
  }
}

async function onSave() {
  saving.value = true;
  try {
    const updated = await authApi.updateMe({
      nickname: form.nickname || null,
      avatar: form.avatar || null,
    });
    auth.user = updated;
    ElMessage.success('资料已更新');
  } finally {
    saving.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <div class="page profile" v-loading="loading">
    <h2>个人资料</h2>
    <div class="card-shadow box">
      <div class="avatar-row">
        <el-avatar :size="72" :src="form.avatar || undefined">
          {{ (auth.user?.nickname || auth.user?.username || '?').charAt(0).toUpperCase() }}
        </el-avatar>
        <div class="ident">
          <div class="uname">
            {{ auth.user?.username }}
            <el-tag v-if="auth.user?.role === 'ADMIN'" size="small" type="danger">管理员</el-tag>
          </div>
          <div class="muted">{{ auth.user?.email }}</div>
        </div>
      </div>

      <el-form label-position="top" @submit.prevent="onSave">
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" maxlength="30" show-word-limit placeholder="展示名称" />
        </el-form-item>
        <el-form-item label="头像 URL">
          <el-input v-model="form.avatar" placeholder="https://..." />
        </el-form-item>
        <el-button type="primary" :loading="saving" native-type="submit">保存</el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.profile {
  max-width: 560px;
}
h2 {
  font-size: 18px;
  margin: 0 0 16px;
}
.box {
  padding: 24px;
}
.avatar-row {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 24px;
}
.uname {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
