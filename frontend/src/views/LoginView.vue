<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const formRef = ref<FormInstance>();
const loading = ref(false);
const form = reactive({ username: '', password: '' });

const rules: FormRules<typeof form> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

async function onSubmit() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    try {
      await auth.login({ username: form.username, password: form.password });
      ElMessage.success('登录成功');
      const redirect = (route.query.redirect as string) || '/map';
      router.replace(redirect);
    } finally {
      loading.value = false;
    }
  });
}
</script>

<template>
  <div class="page auth-page">
    <div class="card-shadow auth-card">
      <h2>登录</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="3–20 位字母 / 数字 / 下划线" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 8 位,含字母与数字" />
        </el-form-item>
        <el-button type="primary" :loading="loading" native-type="submit" class="submit">
          登录
        </el-button>
      </el-form>
      <div class="footer">
        <span class="muted">还没账号?</span>
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 80px;
}
.auth-card {
  width: 380px;
  padding: 32px;
}
.auth-card h2 {
  margin: 0 0 24px;
  font-size: 20px;
}
.submit {
  width: 100%;
}
.footer {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
}
.footer a {
  margin-left: 6px;
  color: #409eff;
}
</style>
