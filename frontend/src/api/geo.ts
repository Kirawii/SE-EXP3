import client from './client';
import type { DistanceOut, NearbyHit, RecommendHit } from '@/types';

export interface NearbyParams {
  lng: number;
  lat: number;
  radius_km?: number;
  limit?: number;
}

export interface BoxParams {
  lng: number;
  lat: number;
  width_km: number;
  height_km: number;
  limit?: number;
}

export const nearby = (params: NearbyParams) =>
  client.get<NearbyHit[]>('/geo/nearby', { params }).then((r) => r.data);

export const box = (params: BoxParams) =>
  client.get<NearbyHit[]>('/geo/box', { params }).then((r) => r.data);

export interface RecommendParams {
  lng: number;
  lat: number;
  radius_km?: number;
  category?: string;
  limit?: number;
}

export const recommend = (params: RecommendParams) =>
  client.get<RecommendHit[]>('/geo/recommend', { params }).then((r) => r.data);

export const distance = (a: string, b: string) =>
  client.get<DistanceOut>('/geo/distance', { params: { a, b } }).then((r) => r.data);

export const geohash = (id: string) =>
  client
    .get<{ id: string; geohash: string }>(`/geo/geohash/${encodeURIComponent(id)}`)
    .then((r) => r.data);

export const position = (id: string) =>
  client
    .get<{ id: string; lng: number; lat: number }>(`/geo/position/${encodeURIComponent(id)}`)
    .then((r) => r.data);
