<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';
import type { FormInstance, FormRules } from 'element-plus';

const auth = useAuthStore();
const router = useRouter();

const formRef = ref<FormInstance>();
const loading = ref(false);
const form = reactive({
  username: '',
  email: '',
  password: '',
  passwordRepeat: '',
  nickname: '',
});

const rules: FormRules<typeof form> = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_]{3,20}$/, message: '3–20 位字母 / 数字 / 下划线', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '至少 8 位', trigger: 'blur' },
    {
      pattern: /(?=.*[A-Za-z])(?=.*\d)/,
      message: '需同时包含字母与数字',
      trigger: 'blur',
    },
  ],
  passwordRepeat: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_r, v, cb) => (v === form.password ? cb() : cb(new Error('两次密码不一致'))),
      trigger: 'blur',
    },
  ],
};

async function onSubmit() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    try {
      await auth.register({
        username: form.username,
        email: form.email,
        password: form.password,
        nickname: form.nickname || undefined,
      });
      await auth.login({ username: form.username, password: form.password });
      ElMessage.success('注册成功');
      router.replace('/map');
    } finally {
      loading.value = false;
    }
  });
}
</script>

<template>
  <div class="page auth-page">
    <div class="card-shadow auth-card">
      <h2>注册</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="昵称(可选)" prop="nickname">
          <el-input v-model="form.nickname" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="passwordRepeat">
          <el-input v-model="form.passwordRepeat" type="password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" native-type="submit" class="submit">
          创建账号
        </el-button>
      </el-form>
      <div class="footer">
        <span class="muted">已有账号?</span>
        <router-link to="/login">直接登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 60px;
}
.auth-card {
  width: 420px;
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
