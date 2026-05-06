import axios, { AxiosError } from 'axios';
import { ElMessage } from 'element-plus';
import type { ApiError } from '@/types';

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 10_000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (resp) => resp,
  (error: AxiosError<ApiError>) => {
    const data = error.response?.data;
    const status = error.response?.status;

    if (status === 401 && (data?.code === 'token_revoked' || data?.code === 'token_invalid')) {
      localStorage.removeItem('access_token');
      if (location.pathname !== '/login') {
        location.assign('/login');
      }
    }

    const msg = data?.message || error.message || '请求失败';
    ElMessage.error(msg);
    return Promise.reject(error);
  },
);

export default client;
