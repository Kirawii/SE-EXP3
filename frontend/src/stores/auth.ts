import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import * as authApi from '@/api/auth';
import type { LoginPayload, RegisterPayload } from '@/api/auth';
import type { User } from '@/types';

export const useAuthStore = defineStore(
  'auth',
  () => {
    const token = ref<string | null>(null);
    const user = ref<User | null>(null);

    const isAuthed = computed(() => !!token.value);
    const isAdmin = computed(() => user.value?.role === 'ADMIN');

    async function login(payload: LoginPayload) {
      const res = await authApi.login(payload);
      token.value = res.access_token;
      user.value = res.user;
      localStorage.setItem('access_token', res.access_token);
    }

    async function register(payload: RegisterPayload) {
      await authApi.register(payload);
    }

    async function fetchMe() {
      if (!token.value) return null;
      const u = await authApi.me();
      user.value = u;
      return u;
    }

    async function logout() {
      try {
        if (token.value) await authApi.logout();
      } finally {
        token.value = null;
        user.value = null;
        localStorage.removeItem('access_token');
      }
    }

    function hydrate() {
      const stored = localStorage.getItem('access_token');
      if (stored && !token.value) token.value = stored;
    }

    return { token, user, isAuthed, isAdmin, login, register, logout, fetchMe, hydrate };
  },
  {
    persist: {
      pick: ['token', 'user'],
    },
  },
);
