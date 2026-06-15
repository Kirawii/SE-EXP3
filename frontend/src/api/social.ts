import client from './client';
import type { Comment, FavoriteState, Landmark } from '@/types';

// ---- 收藏 ----

export const getFavoriteState = (lid: string) =>
  client.get<FavoriteState>(`/landmarks/${encodeURIComponent(lid)}/favorite`).then((r) => r.data);

export const addFavorite = (lid: string) =>
  client.put<FavoriteState>(`/landmarks/${encodeURIComponent(lid)}/favorite`).then((r) => r.data);

export const removeFavorite = (lid: string) =>
  client.delete<FavoriteState>(`/landmarks/${encodeURIComponent(lid)}/favorite`).then((r) => r.data);

export const listFavorites = () =>
  client.get<Landmark[]>('/users/me/favorites').then((r) => r.data);

// ---- 评论 ----

export const listComments = (lid: string) =>
  client.get<Comment[]>(`/landmarks/${encodeURIComponent(lid)}/comments`).then((r) => r.data);

export const addComment = (lid: string, content: string) =>
  client
    .post<Comment>(`/landmarks/${encodeURIComponent(lid)}/comments`, { content })
    .then((r) => r.data);

export const deleteComment = (cid: string) =>
  client.delete<void>(`/comments/${encodeURIComponent(cid)}`).then((r) => r.data);
