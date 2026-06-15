import client from './client';
import type { Landmark, LandmarkCreateIn, LandmarkUpdateIn } from '@/types';

export interface SearchParams {
  q?: string;
  category?: string;
  limit?: number;
}

export const searchLandmarks = (params: SearchParams = {}) =>
  client.get<Landmark[]>('/landmarks', { params }).then((r) => r.data);

export const createLandmark = (payload: LandmarkCreateIn) =>
  client.post<Landmark>('/landmarks', payload).then((r) => r.data);

export const listMine = () => client.get<Landmark[]>('/landmarks/mine').then((r) => r.data);

export const listByCategory = (category: string) =>
  client.get<Landmark[]>(`/landmarks/by-category/${encodeURIComponent(category)}`).then((r) => r.data);

export const getLandmark = (id: string) =>
  client.get<Landmark>(`/landmarks/${encodeURIComponent(id)}`).then((r) => r.data);

export const updateLandmark = (id: string, payload: LandmarkUpdateIn) =>
  client.patch<Landmark>(`/landmarks/${encodeURIComponent(id)}`, payload).then((r) => r.data);

export const deleteLandmark = (id: string) =>
  client.delete<void>(`/landmarks/${encodeURIComponent(id)}`).then((r) => r.data);
