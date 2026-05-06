import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/map' },
    {
      path: '/map',
      name: 'map',
      component: () => import('@/views/MapView.vue'),
    },
    {
      path: '/landmarks',
      name: 'landmark-list',
      component: () => import('@/views/LandmarkListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/landmarks/:id',
      name: 'landmark-detail',
      component: () => import('@/views/LandmarkDetailView.vue'),
      props: true,
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guestOnly: true },
    },
    { path: '/:pathMatch(.*)*', redirect: '/map' },
  ],
});

router.beforeEach((to) => {
  const auth = useAuthStore();
  auth.hydrate();
  if (to.meta.requiresAuth && !auth.isAuthed) {
    return { name: 'login', query: { redirect: to.fullPath } };
  }
  if (to.meta.guestOnly && auth.isAuthed) {
    return { name: 'map' };
  }
});

export default router;
