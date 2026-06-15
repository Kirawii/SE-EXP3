import client from './client';
import type { Landmark, LandmarkStatus, User } from '@/types';

export const listLandmarksByStatus = (status: LandmarkStatus = 'PENDING') =>
  client.get<Landmark[]>('/admin/landmarks', { params: { status } }).then((r) => r.data);

export const reviewLandmark = (lid: string, action: 'approve' | 'reject') =>
  client
    .post<Landmark>(`/admin/landmarks/${encodeURIComponent(lid)}/review`, { action })
    .then((r) => r.data);

export const listUsers = () => client.get<User[]>('/admin/users').then((r) => r.data);

export const disableUser = (uid: string) =>
  client.post<User>(`/admin/users/${encodeURIComponent(uid)}/disable`).then((r) => r.data);

export const enableUser = (uid: string) =>
  client.post<User>(`/admin/users/${encodeURIComponent(uid)}/enable`).then((r) => r.data);

// CSV 导出：直接拿后端的下载地址(带鉴权头需另行处理,这里返回 blob)
export const exportLandmarksCsv = () =>
  client
    .get('/admin/export/landmarks.csv', { responseType: 'blob' })
    .then((r) => r.data as Blob);
